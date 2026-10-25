# nf-codonyat viral iGenomes

AWS iGenomes does not publish entries for HIV-1, HCV, SARS-CoV-2, influenza,
RSV, or HBV. This directory is the nf-codonyat equivalent catalog for those
small viral references. The files are kept in the public repository under
`assets/presets/`; `manifest.json` records their accessions, provenance, and
SHA-256 checksums.

Use an entry with `--genome`, for example:

```bash
nextflow run sjoclaudi/nf-codonyat \
  --genome SARS_COV_2 --input samplesheet.csv --outdir results
```

The default base is the checked-out repository. For a public checkout or a
mirror, `--igenomes_base` may point at a directory or an HTTPS/S3 prefix that
contains the paths in `manifest.json` (for example the repository root URL).
Primer schemes remain assay-specific; entries without a bundled scheme must
be supplied with `--primer_bed` or `--amplicons`.

These references support NGS analysis for infectious-disease research, clinical
assay development, genotype/resistance surveillance, and tools intended to
inform clinical management. The reference catalog itself is not a clinically
validated diagnostic or resistance interpretation system: clinical deployment
requires local analytical/clinical validation, version locking, appropriate
controls, and review by qualified professionals.
