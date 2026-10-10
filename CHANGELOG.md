# Changelog

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
