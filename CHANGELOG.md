# Changelog

## [0.8.1] - 2026-10-24

### Changed
- Task image `ghcr.io/sjoclaudi/nf-codonyat:0.8.1` (codonyat remains **1.3.1**)

### Fixed
- Running without a primer BED no longer crashes `CODONYAT_STRAND` (`ValueError: Amplicon file amplicons_used.tsv contains no definitions`). `amplicons_used.tsv` gets one placeholder row per reference record covering the whole record (#21).
- **influenza-a** HA `NC_026433.1` positions 716 and 719 and NP `NC_026436.1` position 341: IUPAC `R` resolved to `A` (majority CA/07/2009 GenBank CDS; the ARTIC scheme FASTA still has `R`). PA-X annotation extended from `1-570,572-700` to `1-570,572-760` (252 aa plus the natural stop) (#21).
- HBV primer `de464cad_2` removed: insert 1107–1692 duplicates `f3d7635a_2` (#21).
- CI docker job runs `-profile test_hbv` and `-profile test_hcv` (#21).
- Manifest author spelled **Marc Noguera-Julian** (hyphen, no accent) (#21).

## [0.8.0] - 2026-10-22

### Added
- Bundled tiled primer schemes (CC BY-SA 4.0) for **influenza-a** (`artic-flu-a/800/v1.0.0`, draft), **rsv** (`rsva-rsvb/1000/v1.0.0`, tested) and **hbv** (`hbv/600/v2.1.0`). Alt primers collapsed to one `_LEFT`/`_RIGHT` pair per amplicon; 6-column BED; `primer_unverified: false` and `requires_primer_bed: false`. Research use only (#20).
- **influenza-b** preset: B/Lee/1940 RefSeq NC_002204.1–NC_002211.1, taxid 11520, no bundled primers (`requires_primer_bed: false`). Zhou et al. 2014 universal IBV amplification cited in `SOURCES.md` (#20).
- `-profile test_hbv` and `-profile test_hcv`: tiny synthetic pairs exercising the bundled HBV scheme and HCV with no primer BED (#20).

### Changed
- **influenza-a** reference is the artic-flu-a scheme set (CA/07/2009 RefSeq plus avian 1934 polymerase records), not PR8.
- **rsv** is a two-record FASTA (NC_038235.1 RSV-A and NC_001781.1 RSV-B) so BED chrom names match.
- **hbv** reference is scheme X02763 (NCBI X02763.1 rotated to the scheme origin); origin-crossing P/L/PreS2 annotation is kept.
- **hcv** keeps NC_004102.1 and no longer requires `--primer_bed` (Bull et al. 2016 single-amplicon method cited; optional user BED still accepted).
- Primer trimming is skipped when no BED/amplicons are given and `requires_primer_bed` is false (empty `amplicons_used.tsv`, `NO_PRIMERS` warning). Custom mode and HIV-1 / SARS-CoV-2 behaviour are unchanged.
- Origin-crossing primer pairs on circular references (HBV `f3d7635a_5`) are accepted.
- Docs and examples use the single `s3://codonyat` bucket (`samples/`, `results/`, `refdb/`, `nf-work/`) instead of `s3://codonyat-nf-work` / `s3://codonyat-refdb`. `tests/test_infra_json.py` leak-check flags any `s3://` URI and `codonyat/`-style bucket paths, not the plain word in version fields.

## [0.7.0] - 2026-10-17

### Added
- **`-profile awsbatch`**: Spot-only AWS Batch executor (`conf/awsbatch.config`, queue `--awsbatch_queue`, default `codonyat-queue`, region `eu-central-1`). No Wave, Fusion or Seqera token. `s3://` inputs, Kraken2 database prefixes and `--outdir` are supported. Research use only (#14).
- **Schema `x-ui` annotations**: every `nextflow_schema.json` parameter is tagged `basic`, `advanced`, `infra` (shown read-only) or `internal` (hidden) so a SaaS config tab can be built from the schema. Safe `minimum`/`maximum`/`pattern` bounds added (fractions 0–1, percentages 0–100, MAPQ/BQ 0–60, exclusive strand-ratio bounds). `--awsbatch_queue` and `--kraken2_db` are `internal` (queue and bucket paths are never shown). `assets/infra.json` is the read-only pane: Kraken2 database name (last path component only), AWS Batch `process.resourceLimits` (16 CPU / 120 GB / 24 h), region, and pipeline / container / codonyat versions — no S3 URIs, buckets or queue (enforced by `tests/test_infra_json.py`) (#16).
- **Research flag params** (advanced): `--min_baseq` (null / off so TSV/XML stay byte-identical), `--min_freq` (0.01), `--min_coverage` (10), `--sb_alpha` (0.05). The last three are passed to `codonyat-runner` only when `--emit_stats` or `--emit_aavf` is on (they only affect stats/AAVF flags). `--collapsed-read-counts` is not exposed. Default hiv1 / `test_sarscov2` / `test_flua` codon TSV/XML stay byte-identical (#16).

### Changed
- Task image `ghcr.io/sjoclaudi/nf-codonyat:0.7.0` (codonyat remains **1.3.1**)

### Fixed
- Samplesheet, reference, primer, annotation, Kraken2 database and subtype panel paths accept `s3://` URIs; Kraken2 DB prefixes stage as a directory (`hash.k2d`, `opts.k2d`, `taxo.k2d`) (#14).
- `s3://` samplesheet rows are detected via the original URI / `toUriString()` (not `file().toString()`, which is `/bucket/key`); the FASTQ header is not read for remote paths. A remote `--kraken2_db` gets a cheap `exists()` check when credentials allow, otherwise a warning (#14).

## [0.6.0] - 2026-10-16

### Added
- **Opt-in research outputs**: `--emit_stats` and `--emit_aavf` (default `false`) pass `--stats` / `--aavf` to `codonyat-runner` and publish `samples/<id>/<id>.stats.tsv` and `samples/<id>/<id>.aavf`. Off by default so existing codon TSV/XML stay unchanged.
- **`-profile test_flua`**: synthetic A/Puerto Rico/8/1934 HA+NA pairs in custom mode (`--reference`, `--primer_bed`, `--annotation`, `--skip_contamination`)

### Changed
- Updated to codonyat **1.3.1** (read names ending in `_<digits>` are not collapsed unless `--collapsed-read-counts`; nf-codonyat does not pass that flag. Junction codons in multi-part proteins are kept; protein names match exactly. Opt-in Wilson CI / strand-bias / diversity stats and AAVF v1.0 from 1.3.0; default TSV/XML identical to 1.3.0 on uncollapsed names)
- Task image `ghcr.io/sjoclaudi/nf-codonyat:0.6.0`
- Docs and README: research-use-only wording for characterising viral genetic diversity (codon and amino-acid variant frequencies)
- **`-profile test_sarscov2`**: custom mode with unannotated MN908947.3, ARTIC v4.1 BED and GFF3 CDS (synthetic amplicon pairs; `--skip_contamination`)
- **`AMPLICON_NO_CDS`** is a warning, not an error, so a primer scheme may include amplicons that do not overlap an annotated CDS
- Contamination **`OTHER_VIRAL_PCT`** is viruses minus the target clade minus phiX (not minus HIV-1). `HIV1_*` columns are unchanged

### Fixed
- Multi-record iVar consensus: `samtools mpileup -r` so each record's consensus has that record's own length
- Skip the "Reference header lacks protein annotations" warning when `--annotation` is set

### Notes
- Default outputs are unchanged when the new flags are off
- Research use only — characterising viral genetic diversity (codon and amino-acid variant frequencies)

## [0.5.0] - 2026-10-16

### Added
- **Preset system**: Supports hiv1 (default), sars-cov-2, influenza-a, rsv, hbv, hcv, and custom presets
- **Multi-record reference support**: For segmented viruses like influenza A (codonyat 1.2.1)
- **Validation mode**: `--validate_only` for fast input checking without running the full pipeline
- **Generic contamination tracking**: 
  - New parameters: `--target-taxid`, `--target-label`
  - New columns: `TARGET_TAXID`, `TARGET_READS`, `TARGET_PCT` (appended to all contamination tables)
  - HIV1_* columns preserved for backward compatibility
- **Flexible input formats**:
  - `--primer-bed`: 6-column BED format (chrom,start,end,name,pool,strand) with _LEFT/_RIGHT naming
  - `--annotation`: GFF3 (CDS features) or BED (4 columns) format
  - `--amplicons`: TSV format (retained for backward compatibility)
- **New parameters**: 
  - `--preset`: Choose virus preset or custom mode
  - `--contamination-warn-target-pct`: Generic threshold (replaces HIV-specific)
- **New outputs**:
  - `reference/validation.json`: Machine-readable validation results
  - `reference/annotation_used.tsv`: Protein annotation with record and intervals columns
  - `reference/amplicons_used.tsv`: Derived amplicon table
  - `reference/reference_used.fasta`: Annotated reference as passed to codonyat
  - `pipeline_info/run_mode.json`: Pipeline configuration and provenance
- **Input validation**: 100 kb total reference limit, minus-strand CDS rejected, primer pairing, CDS length multiple of 3
- **SARS-CoV-2 ARTIC nCoV-2019 V4.1** primer BED (CC BY 4.0) bundled with MN908947.3
- **Unverified presets** (`influenza-a`, `rsv`, `hbv`, `hcv`): reference only; `--primer_bed` or `--amplicons` required (primers are not invented)
- **`-profile test_sarscov2`**: synthetic MN908947.3 S-gene pairs

### Changed
- Updated to codonyat **1.2.1** (multi-record references and multi-interval proteins; single-pass `--protein all` and comma lists; multi-protein XML identical to 1.1.0 / v0.4.0)
- Task image `ghcr.io/sjoclaudi/nf-codonyat:0.5.0`
- Subtype panel now optional (only HIV-1 preset includes bundled panel); subtype is auto-skipped when no panel is provided
- Contamination auto-skipped in custom mode without Kraken2 database or taxid
- Reference and amplicons no longer universally required (preset-dependent)
- Schema updated to reflect multi-virus support
- `--validate_only` is a real fast path (PREPARE_REFERENCE + CHECK_VALIDATION); `validation.json` is published even when invalid, then the workflow exits non-zero
- Prepared reference/amplicons are value channels (`.first()`) so every samplesheet sample is processed

### Deprecated
- `--contamination-warn-hiv-pct`: Use `--contamination-warn-target-pct` instead (still accepted as alias)

### Notes
- HIV-1 codon TSV/XML and other analysis tables are byte-identical to v0.4.0 except appended `TARGET_*` columns on contamination tables, plus new `reference/` and `pipeline_info/run_mode.json` files (provenance/timestamps / `codonyat: "1.2.1"` may differ)
- `run_mode.json` field `reference_accessions` is always a JSON list
- Research use only — no drug-resistance or clinical interpretation

## [0.4.0] - 2026-10-10

### Added
- nf-core-style metro map of the pipeline (docs/images), embedded in the README.
- nextflow_schema.json covering every parameter, with nf-schema validation and `--help`; samplesheet schema.
- Optional nf-prov provenance (`--prov_enabled`): BCO, provenance DAG and RO-Crate metadata.
- conf/base.config resource labels with retry strategy, `process.resourceLimits`, conf/modules.config, test and test_full profiles, podman profile.
- tower.yml for Seqera Platform, pre-commit config, .editorconfig, .prettierrc, CITATIONS.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md.

### Notes
- Analysis outputs are byte-identical to 0.3.1 on the test profile (see docs/BYTE-IDENTICAL-VERIFICATION.md).

## [0.3.1] - 2026-10-05

### Changed
- codonyat 1.1.0 is now installed from PyPI instead of from a git source.

## [0.3.0] - 2026-10-04

PASeq-style processing steps (design: decisions D1–D13). Research use only: all new outputs are
descriptive; there is no drug-resistance or clinical interpretation.

### Added
- **Contamination report (step 2):** Kraken2 on the trimmed reads (nf-core `kraken2/kraken2`), per-sample
  and combined tables with a warning flag (HIV-1 < 50% of classified or human > 50%; report only, no reads
  removed), Kraken2 section in MultiQC. New params `--kraken2_db` (required for FASTQ unless
  `--skip_contamination`), `--kraken2_confidence`, `--kraken2_memory_mapping`,
  `--contamination_warn_hiv_pct`, `--contamination_warn_human_pct`.
- **Subtype estimate (step 3):** BBSplit (nf-core `bbmap/bbsplit`) against the new panel
  `assets/presets/hiv1_subtype_panel_v1` (pol region; A = 3 A1 references, B = 4 references, M = LANL group M
  consensus; sources, checksums and build script included). `SUBTYPE_ESTIMATE` reports the % of reads per bin,
  a call, the margin and a flag. Params `--subtype_panel`, `--skip_subtype`, `--subtype_min_reads`,
  `--subtype_min_margin`.
- **Read-pair merging (step 5):** BBMerge (nf-core `bbmap/bbmerge`, `ordered=t`) for paired-end samples;
  merged reads (SE) and not-merged pairs (PE) aligned in one Bowtie2 step and combined with
  `samtools merge`. Params `--merge_pairs`, `--bbmerge_args`.
- **Strand metrics from the unmerged reads (D9):** all trimmed pairs are also aligned as pairs, filtered
  and run through codonyat; `STRAND_METRICS` writes `<s>.strand_metrics_unmerged.tsv` and the amino-acid
  table gets `*_UNMERGED` columns. Param `--strand_metrics_unmerged`.
- **Consensus (step 6):** samtools sort + iVar consensus (nf-core `ivar/consensus`; `-t 0.5 -c 0.5 -m 100
  -n N -q 20`, mpileup `-aa -A -B -d 0 -Q 0`): IUPAC codes for mixtures, N below 100x, majority deletions
  applied. `CONSENSUS_REPORT` writes the renamed FASTA, an indel table (applied / frameshift flags) and
  statistics; `consensus_all.fa` and `consensus_stats.tsv` for the run. Params `--skip_consensus`,
  `--consensus_threshold`, `--consensus_min_depth`, `--consensus_insertion_threshold`, `--consensus_min_bq`.
- **Amino-acid tables (D11):** `CODON_TO_AA` → `variants/<s>.aa_variants.tsv` and `aa_variants_summary.tsv`
  (amino-acid frequencies only).
- **Provenance:** `pipeline_info/software_versions.yml` (from the `versions` topic), `provenance.json`
  (versions, all params, SHA-256 of the reference, amplicons, panel and Kraken2 database files) and an
  auto-written `methods.md` with the research-use-only statement. MultiQC carries a research-use-only comment
  and the contamination and subtype tables.
- Multi-protein runs: `--protein` takes one name, a list (`PR,RT,INT`) or `all` (new default); all are
  counted in one codonyat pass. Every listed protein must be annotated in the reference header.
- Input checks: FASTQ samples need `--kraken2_db` unless `--skip_contamination`; a warning when the first
  read header looks like Oxford Nanopore or Ion Torrent (Illumina only, D12).
- `--save_intermediates` publishes trimmed FASTQ, per-part BAMs, the strand-branch outputs, raw iVar output
  and Kraken2 per-read assignments.
- `nextflow_schema.json` describing all parameters.
- Test data: tiny Kraken2 database (`assets/testdata/kraken2_tiny_db`, HXB2 + phiX + human mtDNA, with its
  build script) and `consensus_rules.sam` (mixture → IUPAC, majority deletion, < 100x → N).
- nf-test: PE end-to-end with all steps, SE FASTQ, PE with `--merge_pairs false` and the report steps
  skipped, consensus rules, SAM-only with `--protein RT` (byte-identical to v0.2.0), missing `--kraken2_db`
  and protein-list validation.

### Changed
- codonyat 1.1.0 (streaming, flat memory, multi-protein).
- Task image `ghcr.io/sjoclaudi/nf-codonyat:0.3.0` (adds `procps` for task metrics).
- Bowtie2 always runs with `--reorder`, so the order of rows in the codon tables no longer depends on
  thread scheduling (counts are unchanged).
- `BOWTIE2_BUILD` asks for 2 CPUs / 4 GB instead of the nf-core `process_high` default.
- Default `--protein` is now `all` (was `RT`). Use `--protein RT` to reproduce v0.2.0 outputs.
- README and docs: research-use-only wording; example sample names no longer use "patient".

### Unchanged
- SAM samples skip every FASTQ-only step; with `--protein RT` their codon TSV and XML are byte-identical
  to v0.2.0. Paired-end FASTQ with `--merge_pairs false --protein RT` gives the same codon table as v0.2.0.

## [0.2.0] - unreleased (tag pending)

### Added
- FASTQ input: FastQC (raw reads) → fastp → bowtie2 `--very-sensitive-local` (index built from `--reference`) → sorted BAM.
- Samplesheet columns `sample,fastq_1,fastq_2,sam`; each row has FASTQ or SAM. Old `sample,sam` sheets still work.
- MAPQ/flag filter before codonyat for FASTQ and SAM samples (`--min_mapq 20`, `--exclude_flags 0x904`), with samtools flagstat before and after.
- MultiQC report (FastQC, fastp, bowtie2, flagstat).
- New params `--fastp_args`, `--bowtie2_args`, `--min_mapq`, `--exclude_flags`.
- Real test data for the FASTQ path: HVG286PL subsampled to 2,000 read pairs, plus an `Amp_RT` amplicon (HXB2 2550–3869).
- nf-test cases for the FASTQ path, the old `sample,sam` format and a row with both FASTQ and SAM.

### Changed
- Read-processing steps use nf-core modules (fastqc, fastp, bowtie2/build, bowtie2/align, samtools/view, samtools/flagstat, multiqc), tracked in `modules.json`; local modules moved to `modules/local/`.
- SAM inputs are now filtered (MAPQ ≥ 20, primary mapped only) before codonyat, which itself does no quality filtering (codonyat 1.0.1 only skips unmapped reads). The bundled synthetic SAM results are unchanged.

### Future options (not implemented)
- Primer clipping (e.g. `ivar trim` / `samtools ampliconclip` with a primer BED).
- No duplicate removal is planned for amplicon data (position-based dedup would discard real coverage).

### Fixed
- Pipeline parses and passes `nextflow lint` on Nextflow 25.04+/26.x (strict syntax).
- Removed the output rename loop that overwrote each sample's TSV with the amplicons file.
- Reference and amplicons are value channels, so every sample is processed (not just the first).
- Run no longer hangs after completion (side-effect-only validation channels removed).
- Results publish to `samples/<sample_id>/`; summary published once; reports follow `--outdir`.
- `bin/codonyat_summary.py` is executable.

### Changed
- Software comes from a conda env file or the `ghcr.io/sjoclaudi/nf-codonyat:0.1.0` image; no runtime `pip install`.
- Test data replaced with valid synthetic HXB2 RT amplicon reads (two samples) and a relative samplesheet.
- nf-test 0.9.5 suite with output snapshot; CI runs lint, nf-test and the test profile for docker and conda.
- Repository URLs point to `sjoclaudi/nf-codonyat`.
- Removed the undocumented `hook_url` notification option.

## [0.1.0] — 2026-08-30

### Added
- Initial release
- `CODONYAT_RUN` process wrapping `codonyat-runner`
- `CODONYAT_SUMMARY` process merging per-sample TSVs
- `VALIDATE_INPUT` subworkflow for input checking
- JSON Schema validation for params and samplesheet
- GitHub Actions CI (lint + test)
- Docker and Conda profile support
- Test dataset in `assets/testdata/`
