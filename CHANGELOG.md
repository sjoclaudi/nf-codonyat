# Changelog

## [Unreleased]

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
