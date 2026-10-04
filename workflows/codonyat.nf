/*
 * =========================================================
 *  workflows/codonyat.nf
 *
 *  FASTQ samples (Illumina PE or SE):
 *    FastQC (raw) → fastp
 *      ├─ Kraken2 → contamination report          (report only, --skip_contamination)
 *      ├─ BBSplit vs subtype panel → subtype estimate (report only, --skip_subtype)
 *      └─ PE: BBMerge → Bowtie2 merged (SE) + unmerged (PE) → samtools merge
 *         SE (or --merge_pairs false): Bowtie2 → sorted BAM
 *    PE strand branch (--strand_metrics_unmerged): all trimmed pairs → Bowtie2 PE
 *      → filter → codonyat → strand metrics joined onto the amino-acid table
 *  SAM samples: used as given (skip every FASTQ-only step)
 *  Both:  flagstat → samtools view -q MAPQ -F flags → flagstat
 *           ├─ codonyat (all requested proteins in one pass) → amino-acid table
 *           └─ samtools sort → iVar consensus → consensus report (--skip_consensus)
 *  End:   summaries, provenance (versions, params, checksums, methods.md), MultiQC
 *
 *  Research use only: no drug-resistance or clinical interpretation.
 * =========================================================
 */

include { FASTQC                                  } from '../modules/nf-core/fastqc/main'
include { FASTP                                   } from '../modules/nf-core/fastp/main'
include { KRAKEN2_KRAKEN2                         } from '../modules/nf-core/kraken2/kraken2/main'
include { BBMAP_BBSPLIT                           } from '../modules/nf-core/bbmap/bbsplit/main'
include { BBMAP_BBMERGE                           } from '../modules/nf-core/bbmap/bbmerge/main'
include { BOWTIE2_BUILD                           } from '../modules/nf-core/bowtie2/build/main'
include { BOWTIE2_ALIGN                           } from '../modules/nf-core/bowtie2/align/main'
include { BOWTIE2_ALIGN     as BOWTIE2_ALIGN_STRAND } from '../modules/nf-core/bowtie2/align/main'
include { SAMTOOLS_MERGE    as MERGE_ALIGNMENTS   } from '../modules/nf-core/samtools/merge/main'
include { SAMTOOLS_FLAGSTAT as FLAGSTAT_ALIGNED   } from '../modules/nf-core/samtools/flagstat/main'
include { SAMTOOLS_VIEW     as FILTER_ALIGNMENTS  } from '../modules/nf-core/samtools/view/main'
include { SAMTOOLS_VIEW     as FILTER_STRAND      } from '../modules/nf-core/samtools/view/main'
include { SAMTOOLS_FLAGSTAT as FLAGSTAT_FILTERED  } from '../modules/nf-core/samtools/flagstat/main'
include { SAMTOOLS_SORT     as SORT_FILTERED      } from '../modules/nf-core/samtools/sort/main'
include { IVAR_CONSENSUS                          } from '../modules/nf-core/ivar/consensus/main'
include { MULTIQC                                 } from '../modules/nf-core/multiqc/main'
include { CODONYAT_RUN                            } from '../modules/local/codonyat/run/main.nf'
include { CODONYAT_RUN      as CODONYAT_STRAND    } from '../modules/local/codonyat/run/main.nf'
include { CODONYAT_SUMMARY                        } from '../modules/local/codonyat/summary/main.nf'
include { CONTAMINATION_SUMMARY                   } from '../modules/local/contamination/summary/main.nf'
include { CONTAMINATION_COMBINE                   } from '../modules/local/contamination/combine/main.nf'
include { SUBTYPE_ESTIMATE                        } from '../modules/local/subtype/estimate/main.nf'
include { SUBTYPE_COMBINE                         } from '../modules/local/subtype/combine/main.nf'
include { STRAND_METRICS                          } from '../modules/local/strand/metrics/main.nf'
include { CONSENSUS_REPORT                        } from '../modules/local/consensus/report/main.nf'
include { CODON_TO_AA                             } from '../modules/local/aa/table/main.nf'
include { PROVENANCE                              } from '../modules/local/provenance/write/main.nf'

workflow CODONYAT {
    take:
    fastq_ch        // queue: [ meta, [ fastq_1, (fastq_2) ] ]
    sam_ch          // queue: [ meta, sam ]
    reference_ch    // value: path
    amplicons_ch    // value: path

    main:

    def run_contamination = !params.skip_contamination && params.kraken2_db
    def run_subtype       = !params.skip_subtype
    def run_consensus     = !params.skip_consensus

    // ── FASTQ path: QC and trimming ───────────────────────
    FASTQC(fastq_ch)

    FASTP(
        fastq_ch.map { meta, reads -> tuple(meta, reads, []) },
        false,   // discard_trimmed_pass
        false,   // save_trimmed_fail
        false    // save_merged (BBMerge does the merging below)
    )
    trimmed = FASTP.out.reads

    // ── Step 2: contamination report (Kraken2, report only) ──
    contamination_mqc = channel.empty()
    kraken2_reports   = channel.empty()
    if (run_contamination) {
        KRAKEN2_KRAKEN2(
            trimmed,
            file(params.kraken2_db, checkIfExists: true),
            false,                     // save_output_fastqs
            params.save_intermediates  // save_reads_assignment
        )
        kraken2_reports = KRAKEN2_KRAKEN2.out.report
        CONTAMINATION_SUMMARY(kraken2_reports)
        CONTAMINATION_COMBINE(CONTAMINATION_SUMMARY.out.tsv.map { _meta, f -> f }.collect())
        contamination_mqc = CONTAMINATION_COMBINE.out.mqc
    }

    // ── Step 3: subtype estimate (BBSplit vs panel, report only) ──
    // The panel folder holds <bin>.fa per bin and panel.tsv (first column = bin).
    // BBSplit names the first bin "primary"; SUBTYPE_ESTIMATE maps it back.
    subtype_mqc = channel.empty()
    if (run_subtype) {
        def panel_dir = file(params.subtype_panel, checkIfExists: true)
        def bins = panel_dir.resolve('panel.tsv').readLines().drop(1)
            .findAll { line -> line.trim() }
            .collect { line -> line.split('\t')[0] }
            .unique()
        def primary = bins[0]
        def others  = bins.drop(1)
        BBMAP_BBSPLIT(
            trimmed,
            [],                                                            // no pre-built index (panel is ~25 kb)
            panel_dir.resolve("${primary}.fa"),
            tuple(others, others.collect { b -> panel_dir.resolve("${b}.fa") }),
            false                                                          // only_build_index
        )
        SUBTYPE_ESTIMATE(BBMAP_BBSPLIT.out.stats, primary, bins)
        SUBTYPE_COMBINE(SUBTYPE_ESTIMATE.out.tsv.map { _meta, f -> f }.collect())
        subtype_mqc = SUBTYPE_COMBINE.out.mqc
    }

    // ── Steps 4–5: merge pairs, then one Bowtie2 pass ─────
    reference_meta = reference_ch.map { fasta -> tuple([id: fasta.baseName], fasta) }
    BOWTIE2_BUILD(reference_meta)

    trimmed_by_layout = trimmed.branch { meta, _reads ->
        merge: !meta.single_end && params.merge_pairs
        as_is: true
    }

    BBMAP_BBMERGE(trimmed_by_layout.merge, false)   // interleave = false (R1 and R2 files)

    // merged reads → SE ; not-merged pairs → PE ; SE samples / unmerged runs → as given
    to_align = channel.empty()
        .mix(BBMAP_BBMERGE.out.merged.map   { meta, fq -> tuple(meta + [single_end: true,  part: 'merged'],   fq) })
        .mix(BBMAP_BBMERGE.out.unmerged.map { meta, fq -> tuple(meta + [single_end: false, part: 'unmerged'], fq) })
        .mix(trimmed_by_layout.as_is.map    { meta, fq -> tuple(meta + [part: null], fq) })

    BOWTIE2_ALIGN(
        to_align,
        BOWTIE2_BUILD.out.index,
        reference_meta,
        false,   // save_unaligned
        true     // sort_bam
    )

    // restore the sample's own meta (drop the per-part fields)
    aligned_parts = BOWTIE2_ALIGN.out.bam.map { meta, bam ->
        def sample_meta = meta.findAll { k, _v -> k != 'part' } + [single_end: meta.part ? false : meta.single_end]
        tuple(sample_meta, meta.part, bam)
    }
    parts_by_kind = aligned_parts.branch { _meta, part, _bam ->
        split: part
        whole: true
    }
    MERGE_ALIGNMENTS(
        parts_by_kind.split
            .map { meta, _part, bam -> tuple(meta, bam) }
            .groupTuple(size: 2)
            .map { meta, bams -> tuple(meta, bams.sort { b -> b.name }, []) },
        [[:], [], [], []],   // fasta, fai, gzi
        ''                   // no index
    )
    fastq_alignments = MERGE_ALIGNMENTS.out.bam
        .mix(parts_by_kind.whole.map { meta, _part, bam -> tuple(meta, bam) })

    // ── Both paths: MAPQ / flag filter ────────────────────
    alignments = fastq_alignments.mix(sam_ch)

    FLAGSTAT_ALIGNED(alignments.map { meta, aln -> tuple(meta, aln, []) })

    FILTER_ALIGNMENTS(
        alignments.map { meta, aln -> tuple(meta, aln, []) },
        [[:], [], []],   // fasta, fai
        [[:], []],       // qname
        [[:], []],       // bed
        ''               // index_format (SAM output is not indexed)
    )
    filtered = FILTER_ALIGNMENTS.out.sam

    FLAGSTAT_FILTERED(filtered.map { meta, sam -> tuple(meta, sam, []) })

    // ── Step 7: codonyat (all requested proteins, one pass) ──
    CODONYAT_RUN(filtered, reference_ch, amplicons_ch)

    // ── D9 strand branch: all trimmed pairs (pre-merge) aligned as pairs ──
    strand_tables = channel.empty()
    if (params.merge_pairs && params.strand_metrics_unmerged) {
        BOWTIE2_ALIGN_STRAND(
            trimmed.filter { meta, _reads -> !meta.single_end },
            BOWTIE2_BUILD.out.index,
            reference_meta,
            false,
            true
        )
        FILTER_STRAND(
            BOWTIE2_ALIGN_STRAND.out.bam.map { meta, bam -> tuple(meta, bam, []) },
            [[:], [], []],
            [[:], []],
            [[:], []],
            ''
        )
        CODONYAT_STRAND(FILTER_STRAND.out.sam, reference_ch, amplicons_ch)
        STRAND_METRICS(
            CODONYAT_RUN.out.results.map { meta, tsv, _xml -> tuple(meta.id, meta, tsv) }
                .join(CODONYAT_STRAND.out.results.map { meta, tsv, _xml -> tuple(meta.id, tsv) })
                .map { _id, meta, merged_tsv, unmerged_tsv -> tuple(meta, merged_tsv, unmerged_tsv) }
        )
        strand_tables = STRAND_METRICS.out.tsv
    }

    // ── Amino-acid tables (frequencies only, D11) ─────────
    CODON_TO_AA(
        CODONYAT_RUN.out.results.map { meta, tsv, _xml -> tuple(meta.id, meta, tsv) }
            .join(strand_tables.map { meta, tsv -> tuple(meta.id, tsv) }, remainder: true)
            .map { _id, meta, tsv, strand -> tuple(meta, tsv, strand ?: []) },
        reference_ch
    )
    aa_summary = CODON_TO_AA.out.tsv
        .map { _meta, f -> f }
        .collectFile(name: 'aa_variants_summary.tsv', keepHeader: true, skip: 1, sort: { f -> f.name }, storeDir: "${params.outdir}/variants")

    all_tsvs = CODONYAT_RUN.out.results
        .map { _meta, tsv, _xml -> tsv }
        .collect()

    CODONYAT_SUMMARY(all_tsvs)

    // ── Step 6: consensus (iVar; IUPAC; N below min depth) ──
    consensus_fasta = channel.empty()
    if (run_consensus) {
        SORT_FILTERED(filtered, [[:], [], []], '')
        IVAR_CONSENSUS(SORT_FILTERED.out.bam, reference_ch, true)
        CONSENSUS_REPORT(
            IVAR_CONSENSUS.out.fasta.join(IVAR_CONSENSUS.out.mpileup),
            reference_ch.map { fasta -> fasta.withReader { r -> r.readLine() }.substring(1).tokenize(' ')[0] }
        )
        consensus_fasta = CONSENSUS_REPORT.out.fasta
            .map { _meta, f -> f }
            .collectFile(name: 'consensus_all.fa', sort: { f -> f.name }, storeDir: "${params.outdir}/consensus")
        CONSENSUS_REPORT.out.stats
            .map { _meta, f -> f }
            .collectFile(name: 'consensus_stats.tsv', keepHeader: true, skip: 1, sort: { f -> f.name }, storeDir: "${params.outdir}/consensus")
    }

    // ── MultiQC ───────────────────────────────────────────
    multiqc_files = channel.empty()
        .mix(FASTQC.out.zip.map { _meta, f -> f })
        .mix(FASTP.out.json.map { _meta, f -> f })
        .mix(kraken2_reports.map { _meta, f -> f })
        .mix(BBMAP_BBMERGE.out.ihist.map { _meta, f -> f })
        .mix(BOWTIE2_ALIGN.out.log.map { _meta, f -> f })
        .mix(FLAGSTAT_ALIGNED.out.flagstat.map { _meta, f -> f })
        .mix(FLAGSTAT_FILTERED.out.flagstat.map { _meta, f -> f })
        .mix(contamination_mqc)
        .mix(subtype_mqc)
        .collect()

    MULTIQC(
        multiqc_files.map { files -> tuple([id: 'multiqc'], files, [], [], [], []) }
    )

    // ── Provenance: versions, params, checksums, methods.md ──
    versions_tsv = channel.topic('versions')
        .mix(MULTIQC.out.versions)   // MultiQC stays off the topic (nf-core convention)
        .map { process, tool, version -> "${process.tokenize(':').last()}\t${tool}\t${version.toString().trim()}" }
        .unique()
        .collectFile(name: 'versions.tsv', newLine: true, sort: true)
    params_tsv = channel.value(
        params.findAll { k, _v -> !(k as String).contains('-') }
            .collect { k, v -> "${k}\t${v}" }
            .sort()
            .join('\n')
    ).collectFile(name: 'params.tsv', newLine: true)

    PROVENANCE(
        versions_tsv,
        params_tsv,
        reference_ch,
        amplicons_ch,
        run_subtype ? file(params.subtype_panel) : [],
        run_contamination ? file(params.kraken2_db) : []
    )

    emit:
    per_sample = CODONYAT_RUN.out.results        // [ meta, tsv, xml ]
    summary    = CODONYAT_SUMMARY.out.combined_tsv
    aa_summary = aa_summary
    consensus  = consensus_fasta
    multiqc    = MULTIQC.out.report
}
