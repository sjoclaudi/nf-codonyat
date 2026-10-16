# nf-codonyat — Output Description

> Research use only. The pipeline characterises viral genetic diversity (codon and amino-acid
> variant frequencies). All tables are descriptive (counts, frequencies, coverage, QC).

## Directory Structure

```
results/
├── codonyat_summary.tsv          # Combined codon table (all samples, all requested proteins)
├── samples/<s>/
│   ├── <s>.tsv                   # Per-codon table (codonyat)
│   ├── <s>.xml                   # Per-position counts (codonyat)
│   ├── <s>.stats.tsv             # Opt-in (--emit_stats): Wilson CI, strand-bias, diversity
│   └── <s>.aavf                  # Opt-in (--emit_aavf): AAVF v1.0 (research use only)
├── variants/
│   ├── <s>.aa_variants.tsv       # Amino-acid frequencies per protein position
│   └── aa_variants_summary.tsv   # All samples
├── consensus/
│   ├── <s>.consensus.fa          # iVar consensus (IUPAC for mixtures, N below min depth)
│   ├── <s>.consensus_indels.tsv  # Indels seen at >= 5% and whether they are in the consensus
│   ├── <s>.consensus_stats.tsv   # Length, N count, IUPAC count, positions at min depth
│   ├── consensus_all.fa          # All consensus sequences
│   └── consensus_stats.tsv       # All samples
├── contamination/                # FASTQ samples (unless --skip_contamination or auto-skipped)
│   ├── <s>.kraken2.report.txt    # Kraken2 report
│   ├── <s>.contamination.tsv     # % per group + warning flag + TARGET_* columns
│   └── contamination_summary.tsv
├── subtype/                      # FASTQ samples (unless --skip_subtype or no panel)
│   ├── <s>.subtype.tsv           # % reads per panel bin + call/flag
│   ├── subtype_summary.tsv
│   └── bbsplit/<s>.stats.txt     # BBSplit refstats
├── reference/                    # Input validation and provenance
│   ├── validation.json           # Validation results (--validate_only)
│   ├── annotation_used.tsv       # Protein annotation with record and intervals
│   ├── amplicons_used.tsv        # Derived 7-column amplicon table
│   └── reference_used.fasta      # Annotated reference passed to codonyat
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
    ├── run_mode.json             # Pipeline configuration (preset, target, reference accessions, checksums)
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

## Opt-in stats (`samples/{sample}/{sample}.stats.tsv`)

Published only with `--emit_stats`. Written by codonyat (`--stats`). Research use only:
Wilson 95% CI, strand-bias p-value, flags and diversity indices. Default TSV/XML are unchanged
whether this flag is on or off.

| Column | Description |
|--------|-------------|
| `LEVEL` | Row level (`variant`, `codon` or `gene`) |
| `FILE` / `REFERENCE` / `RECORD` / `PROTEIN` | Sample file, reference and protein |
| `POSITION` / `AA_POS` | Nucleotide coordinate and 1-based amino-acid position |
| `VARIANT` / `AA` | Observed codon and translated amino acid |
| `COUNT` / `FREQ` | Count and frequency |
| `FREQ_CI_LOW` / `FREQ_CI_HIGH` | Wilson 95% confidence interval |
| `FW` / `RV` / `SB_P` | Strand counts and Fisher exact strand-bias p-value |
| `FLAGS` | `lowfreq`, `sb`, `lowcov` (or empty) |
| `COVERAGE` | Depth at the codon |
| `SHANNON` / `SHANNON_NORM` / `GINI_SIMPSON` / `PI_NT` / `PI_AA` / `N_TYPES` / `N_CODONS` | Diversity indices |

## Opt-in AAVF (`samples/{sample}/{sample}.aavf`)

Published only with `--emit_aavf`. AAVF v1.0 from codonyat (`--aavf`). Research use only.
`##source` includes `research use only`. CAT and SRVL fields are omitted. Default TSV/XML are
unchanged whether this flag is on or off.

## Amino-acid table (`variants/{sample}.aa_variants.tsv`)

One row per protein position and observed amino acid. Codon frequencies that translate to the same amino
acid are summed.

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
`BACTERIA_PCT`, `OTHER_VIRAL_PCT`, `OTHER_PCT`, `WARNING`, `TARGET_TAXID`, `TARGET_READS`, `TARGET_PCT`.

**New in v0.5.0:** `TARGET_TAXID`, `TARGET_READS`, `TARGET_PCT` columns are appended. For the hiv1 preset,
`TARGET_TAXID=11676` and `TARGET_PCT` matches `HIV1_PCT`. For custom mode without a target taxid, these
columns are empty. The `HIV1_*` columns are preserved for v0.4.0 compatibility.
`OTHER_VIRAL_PCT` is the Viruses clade minus the target clade minus phiX (not minus HIV-1 unless
HIV-1 is the target).

The warning lists issues (e.g. `no_reads`, `{target_label}<{threshold}%_of_classified`, `human>50%`),
separated by `;` (`none` if no warnings). Percentages are informative only: no reads are removed and the
pipeline never stops a sample for contamination.

## Subtype estimate (`subtype/{sample}.subtype.tsv`)

One row per panel bin: `READS` (assigned unambiguously to the bin), `PCT_OF_ASSIGNED`, `AMBIGUOUS_READS`
(BBSplit's ambiguous count for the bin), and per sample `CALL` (top bin, or `undetermined` below
`--subtype_min_reads`), `RUNNER_UP`, `MARGIN_PCT_POINTS`, `ASSIGNED_READS`, `AMBIGUOUS_FRACTION` and `FLAG`
(`none`, `fewer_than_<n>_assigned_reads` or `ambiguous_or_possible_recombinant`). The M bin is the group M
consensus and is labelled "group M, not assigned to A or B". This is a read-mapping based estimate for
research use, not a genotyping result.

The `subtype/` folder is omitted when `--skip_subtype` is set or the preset has no panel (everything except
hiv1, unless you pass `--subtype_panel`).

## Reference artefacts (`reference/`)

Written by `PREPARE_REFERENCE` on every run, including `--validate_only`.

### `validation.json`

```json
{"valid": true, "errors": [], "warnings": []}
```

Each error or warning: `code`, `file`, `line` (null if not a file line), `message`. The process that writes
this file always succeeds so the JSON is published; `CHECK_VALIDATION` then exits 1 when `valid` is false.

### `annotation_used.tsv`

| Column | Description |
|--------|-------------|
| `record` | FASTA record id |
| `protein` | Protein name |
| `description` | From the FASTA header, GFF `product`, or TSV |
| `intervals` | 1-based inclusive ranges, `;`-joined when a CDS has several intervals (e.g. `266-13468;13468-21555`) |
| `strand` | `+` (minus-strand CDS is rejected) |
| `start` / `end` | First and last coordinate across the joined intervals |
| `length_aa` | Joined nucleotide length / 3 |
| `source` | `header`, `gff`, `bed` or `tsv` |

### `amplicons_used.tsv`

Seven columns: `label`, `protein`, `reference`, `5p_seq`, `3p_seq`, `start`, `end` (1-based inclusive insert
coordinates). From `--amplicons` or derived from a 6-column `--primer_bed`.

### `reference_used.fasta`

The normalised FASTA actually given to Bowtie2 / codonyat / iVar. Headers use the codonyat 1.2.0 form
`Name(Description):start-end,start-end` (`;` between proteins, `,` between intervals of one protein).

## `pipeline_info/run_mode.json`

| Field | Notes |
|-------|-------|
| `pipeline_version` | Manifest version (0.6.0) |
| `preset` | `hiv1` / `sars-cov-2` / … / `custom` |
| `target_taxid` | Integer or `null` |
| `target_label` | Display label or `null` |
| `reference_accessions` | **Always a JSON list** of FASTA record ids in file order |
| `reference_sha256` | SHA-256 of the input `--reference` (or preset FASTA) |
| `primer_file_sha256` | SHA-256 of `--primer_bed` or `--amplicons` |
| `annotation_sha256` | SHA-256 of `--annotation`, or `null` when the FASTA header is used |
| `kraken2_skipped` | Boolean |
| `kraken2_skip_reason` | `skip_contamination`, `custom_mode_no_kraken2_db`, `custom_mode_no_target_taxid`, `no_kraken2_db`, or `null` |
| `subtype_skipped` | Boolean |
