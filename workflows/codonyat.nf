/*
 * =========================================================
 *  workflows/codonyat.nf
 *
 *  FASTQ samples:  FastQC (raw) → fastp → bowtie2 (sorted BAM)
 *  SAM samples:    used as given
 *  Both:           samtools flagstat → samtools view -q MAPQ -F flags
 *                  → samtools flagstat → codonyat → merged summary
 *  End:            MultiQC (FastQC, fastp, bowtie2, flagstat)
 * =========================================================
 */

include { FASTQC                                  } from '../modules/nf-core/fastqc/main'
include { FASTP                                   } from '../modules/nf-core/fastp/main'
include { BOWTIE2_BUILD                           } from '../modules/nf-core/bowtie2/build/main'
include { BOWTIE2_ALIGN                           } from '../modules/nf-core/bowtie2/align/main'
include { SAMTOOLS_FLAGSTAT as FLAGSTAT_ALIGNED   } from '../modules/nf-core/samtools/flagstat/main'
include { SAMTOOLS_VIEW     as FILTER_ALIGNMENTS  } from '../modules/nf-core/samtools/view/main'
include { SAMTOOLS_FLAGSTAT as FLAGSTAT_FILTERED  } from '../modules/nf-core/samtools/flagstat/main'
include { MULTIQC                                 } from '../modules/nf-core/multiqc/main'
include { CODONYAT_RUN                            } from '../modules/local/codonyat/run/main.nf'
include { CODONYAT_SUMMARY                        } from '../modules/local/codonyat/summary/main.nf'

workflow CODONYAT {
    take:
    fastq_ch        // queue: [ meta, [ fastq_1, (fastq_2) ] ]
    sam_ch          // queue: [ meta, sam ]
    reference_ch    // value: path
    amplicons_ch    // value: path

    main:

    // ── FASTQ path ────────────────────────────────────────
    FASTQC(fastq_ch)

    FASTP(
        fastq_ch.map { meta, reads -> tuple(meta, reads, []) },
        false,   // discard_trimmed_pass
        false,   // save_trimmed_fail
        false    // save_merged (read pairs are never merged: codonyat needs each read's strand)
    )

    reference_meta = reference_ch.map { fasta -> tuple([id: fasta.baseName], fasta) }
    BOWTIE2_BUILD(reference_meta)

    BOWTIE2_ALIGN(
        FASTP.out.reads,
        BOWTIE2_BUILD.out.index,
        reference_meta,
        false,   // save_unaligned
        true     // sort_bam
    )

    // ── Both paths: MAPQ / flag filter before codonyat ────
    alignments = BOWTIE2_ALIGN.out.bam.mix(sam_ch)

    FLAGSTAT_ALIGNED(alignments.map { meta, aln -> tuple(meta, aln, []) })

    FILTER_ALIGNMENTS(
        alignments.map { meta, aln -> tuple(meta, aln, []) },
        [[:], [], []],   // fasta, fai
        [[:], []],       // qname
        [[:], []],       // bed
        ''               // index_format (SAM output is not indexed)
    )

    FLAGSTAT_FILTERED(FILTER_ALIGNMENTS.out.sam.map { meta, sam -> tuple(meta, sam, []) })

    // ── codonyat ──────────────────────────────────────────
    CODONYAT_RUN(FILTER_ALIGNMENTS.out.sam, reference_ch, amplicons_ch)

    all_tsvs = CODONYAT_RUN.out.results
        .map { _meta, tsv, _xml -> tsv }
        .collect()

    CODONYAT_SUMMARY(all_tsvs)

    // ── MultiQC ───────────────────────────────────────────
    multiqc_files = channel.empty()
        .mix(FASTQC.out.zip.map { _meta, f -> f })
        .mix(FASTP.out.json.map { _meta, f -> f })
        .mix(BOWTIE2_ALIGN.out.log.map { _meta, f -> f })
        .mix(FLAGSTAT_ALIGNED.out.flagstat.map { _meta, f -> f })
        .mix(FLAGSTAT_FILTERED.out.flagstat.map { _meta, f -> f })
        .collect()

    MULTIQC(
        multiqc_files.map { files -> tuple([id: 'multiqc'], files, [], [], [], []) }
    )

    emit:
    per_sample = CODONYAT_RUN.out.results        // [ meta, tsv, xml ]
    summary    = CODONYAT_SUMMARY.out.combined_tsv
    multiqc    = MULTIQC.out.report
}
