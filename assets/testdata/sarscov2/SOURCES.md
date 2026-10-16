# SARS-CoV-2 test data

Research use only.

Synthetic Illumina-like paired-end reads (150 bp, insert 250, seed 20261016)
taken from MN908947.3 spike (S) coordinates 21563-25384. Not a clinical
dataset; generated so CI can exercise `--preset sars-cov-2` and the ARTIC
v4.1 primer BED without downloading ENA/SRA runs.

- Reference / primers: see `assets/presets/sars-cov-2/SOURCES.md` (MN908947.3,
  ARTIC nCoV-2019 V4.1, CC BY 4.0).
- Contamination is skipped in `-profile test_sarscov2` (no SARS-CoV-2 Kraken2
  database is bundled). Rebuild a tiny Kraken2 DB with taxid 2697049 to
  exercise TARGET_* columns for this virus.
