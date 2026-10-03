# Changelog

## [Unreleased]

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
