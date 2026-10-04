# nf-codonyat — Output Description

> Research use only. All tables are descriptive (counts, frequencies, coverage, QC). None of them
> contains drug-resistance or clinical interpretation.

## Directory Structure

```
results/
├── codonyat_summary.tsv          # Combined codon table (all samples, all requested proteins)
├── samples/<s>/
│   ├── <s>.tsv                   # Per-codon table (codonyat)
│   └── <s>.xml                   # Per-position counts (codonyat)
├── variants/
│   ├── <s>.aa_variants.tsv       # Amino-acid frequencies per protein position
│   └── aa_variants_summary.tsv   # All samples
├── consensus/
│   ├── <s>.consensus.fa          # iVar consensus (IUPAC for mixtures, N below min depth)
│   ├── <s>.consensus_indels.tsv  # Indels seen at >= 5% and whether they are in the consensus
│   ├── <s>.consensus_stats.tsv   # Length, N count, IUPAC count, positions at min depth
│   ├── consensus_all.fa          # All consensus sequences
│   └── consensus_stats.tsv       # All samples
├── contamination/                # FASTQ samples (unless --skip_contamination)
│   ├── <s>.kraken2.report.txt    # Kraken2 report
│   ├── <s>.contamination.tsv     # % per group + warning flag
│   └── contamination_summary.tsv
├── subtype/                      # FASTQ samples (unless --skip_subtype)
│   ├── <s>.subtype.tsv           # % reads per panel bin + call/flag
│   ├── subtype_summary.tsv
│   └── bbsplit/<s>.stats.txt     # BBSplit refstats
├── merge/                        # Paired-end samples with --merge_pairs
│   ├── <s>.bbmerge.log           # BBMerge log (pairs, joined %)
│   └── <s>_ihist.txt             # Insert-size histogram
├── strand/                       # Paired-end samples with --merge_pairs and --strand_metrics_unmerged
│   ├── <s>.strand_metrics_unmerged.tsv
│   └── <s>.pairs.bowtie2.log     # Alignment of all trimmed pairs (before merging)
├── fastqc/                       # FASTQ samples: FastQC on raw reads
├── fastp/                        # FASTQ samples: fastp HTML/JSON/log
├── alignment/
│   ├── <s>.bam                   # Coordinate-sorted alignment (FASTQ samples; merged + not-merged reads for PE)
│   ├── <s>.merged.bowtie2.log    # PE: merged reads (aligned single-end)
│   ├── <s>.unmerged.bowtie2.log  # PE: pairs BBMerge did not merge (aligned paired-end)
│   ├── <s>.bowtie2.log           # SE samples, or PE with --merge_pairs false
│   └── flagstat/
│       ├── <s>.aligned.flagstat  # before the MAPQ/flag filter
│       └── <s>.filtered.flagstat # after it (what codonyat and iVar see)
├── multiqc/
│   ├── multiqc_report.html       # FastQC, fastp, Kraken2, BBMerge, Bowtie2, flagstat, contamination and subtype tables
│   └── multiqc_report_data/
└── pipeline_info/
    ├── software_versions.yml     # Tool versions per process
    ├── provenance.json           # Versions, all parameters, SHA-256 of reference, amplicons, panel and Kraken2 DB files
    ├── methods.md                # Auto-written methods paragraph (with the research-use-only statement)
    ├── execution_timeline.html
    ├── execution_report.html
    ├── execution_trace.txt
    └── pipeline_dag.html
```

The filtered alignments passed to codonyat are not published (they are the BAM/SAM above minus reads
with MAPQ < `--min_mapq` and flags in `--exclude_flags`); the two flagstat files show what was removed.
`--save_intermediates` also publishes trimmed FASTQ, the per-part BAMs, the strand-branch BAM and codon
table, the raw iVar output and Kraken2 per-read assignments.

## Per-Sample TSV (`{sample}.tsv`)

Columns:

| Column | Description |
|--------|-------------|
| `FILE` | Alignment file name codonyat read (always `<sample>.sam`) |
| `REFERENCE` | Reference sequence ID |
| `PROTEIN` | Protein name (one of the proteins requested with `--protein`) |
| `VARIANT` | Observed codon (e.g. `GTG`; `---` for a codon deletion) |
| `POSITION` | Reference coordinate of the codon's first base (e.g. HXB2 `3099` = RT codon 184) |
| `FREQ` | Variant frequency as a percentage of total depth |
| `FWCOV` | Forward-strand depth at this codon |
| `RVCOV` | Reverse-strand depth at this codon |
| `TOTALCOV` | Total coverage at this codon position |
| `RATIO` | Forward / reverse depth ratio at this codon |

## Combined Summary (`codonyat_summary.tsv`)

Same columns as above, plus:

| Column | Description |
|--------|-------------|
| `SAMPLE` | Sample identifier (from the samplesheet) |

## Per-position XML (`{sample}.xml`)

Per-position counts in a `<SamContainer>` XML tree. With one protein the layout is the same as in
v0.2.0 (below). With several proteins each protein's positions sit inside a `<Protein name="RT">` element.

```xml
<SamContainer sample="sample1.sam" reference="K03455|HIVHXB2CG">
  <Position index="3099">
    <Depth>150</Depth>
    <FwCover>78</FwCover>
    <RvCover>72</RvCover>
    <Variants>
      <Variant codon="ATG" count="3" fw_reads="2" rv_reads="1"/>
      <Variant codon="GTG" count="147" fw_reads="76" rv_reads="71"/>
    </Variants>
  </Position>
</SamContainer>
```

## Amino-acid table (`variants/{sample}.aa_variants.tsv`)

One row per protein position and observed amino acid. Codon frequencies that translate to the same amino
acid are summed. No drug, resistance or clinical annotation.

| Column | Description |
|--------|-------------|
| `SAMPLE` | Sample identifier |
| `PROTEIN` | Protein name |
| `AA_POSITION` | Codon number within the protein (1-based) |
| `NT_POSITION` | Reference coordinate of the codon's first base |
| `REF_CODON` / `REF_AA` | Reference codon and amino acid |
| `AA` | Observed amino acid (`*` stop; `del` codon deletion; `X` partial gap or non-ACGT base) |
| `FREQ` | Summed frequency (%) of the codons coding for `AA` |
| `CODONS` | Contributing codons with their frequencies (`codon:freq,...`) |
| `TOTALCOV`, `FWCOV`, `RVCOV`, `RATIO` | Depth and strand metrics at the codon (from the main alignment) |
| `*_UNMERGED` | Paired-end samples with the strand branch: `FWCOV_UNMERGED`, `RVCOV_UNMERGED`, `TOTALCOV_UNMERGED`, `RATIO_UNMERGED` from the alignment of all trimmed pairs before merging |

With merged reads, `FWCOV`/`RVCOV`/`RATIO` describe fragment orientation (a merged read is written in R1's
orientation); the `*_UNMERGED` columns give the usual read-strand metrics.

## Strand metrics (`strand/{sample}.strand_metrics_unmerged.tsv`)

One row per protein codon position: `FWCOV`, `RVCOV`, `TOTALCOV`, `RATIO` from the main (merged-read)
alignment and the same four values with the `_UNMERGED` suffix from the pre-merge pair alignment.

## Consensus

- `{sample}.consensus.fa`: header `>{sample}|{reference id}|t{threshold}_m{min depth}`. IUPAC codes where
  more than one base is needed to reach `--consensus_threshold`; `N` below `--consensus_min_depth`;
  majority insertions and deletions applied (the sequence can be shorter or longer than the reference).
- `{sample}.consensus_indels.tsv`: `POSITION` (reference coordinate: first deleted base for deletions,
  the base after which an insertion sits), `TYPE`, `LENGTH`, `SEQUENCE`, `COUNT`, `DEPTH`, `FREQ`,
  `APPLIED` (expected in the consensus: frequency at or above the threshold and depth at or above the
  minimum), `FRAMESHIFT` (length not a multiple of 3, per event).
- `{sample}.consensus_stats.tsv`: `CONSENSUS_LENGTH`, `N_COUNT`, `PCT_N`, `IUPAC_AMBIGUOUS`,
  `POSITIONS_AT_MIN_DEPTH`, `THRESHOLD`, `MIN_DEPTH`.

## Contamination (`contamination/{sample}.contamination.tsv`)

Percentages of all read fragments given to Kraken2 (a pair counts once): `TOTAL_FRAGMENTS`,
`UNCLASSIFIED_PCT`, `CLASSIFIED_PCT`, `HIV1_PCT`, `HIV1_PCT_OF_CLASSIFIED`, `HUMAN_PCT`, `PHIX_PCT`,
`BACTERIA_PCT`, `OTHER_VIRAL_PCT`, `OTHER_PCT` and `WARNING` (`none`, or which threshold was crossed).
Report only: no reads are removed.

## Subtype estimate (`subtype/{sample}.subtype.tsv`)

One row per panel bin: `READS` (assigned unambiguously to the bin), `PCT_OF_ASSIGNED`, `AMBIGUOUS_READS`
(BBSplit's ambiguous count for the bin), and per sample `CALL` (top bin, or `undetermined` below
`--subtype_min_reads`), `RUNNER_UP`, `MARGIN_PCT_POINTS`, `ASSIGNED_READS`, `AMBIGUOUS_FRACTION` and `FLAG`
(`none`, `fewer_than_<n>_assigned_reads` or `ambiguous_or_possible_recombinant`). The M bin is the group M
consensus and is labelled "group M, not assigned to A or B". This is a read-mapping based estimate for
research use, not a genotyping result.
