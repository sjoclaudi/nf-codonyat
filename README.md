# nf-codonyat

**Codon-aware amino acid variant typing — Nextflow pipeline**

Wraps the [`codonyat`](https://github.com/mnoguera/codonyat) Python package into a production-ready Nextflow pipeline for viral amplicon NGS analysis.

---

## Overview

`nf-codonyat` takes a SAM file of aligned reads, an annotated reference FASTA, and an amplicon definitions file, then produces per-codon variant frequency tables (TSV) and a diagnostics file (XML).

**Typical use case:** HIV drug-resistance genotyping from deep sequencing of viral amplicons.

---

## Quick Start

```bash
# 1. Install Nextflow
curl -s https://get.nextflow.io | bash

# 2. Run with Docker
nextflow run mnoguera/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference reference.fasta \
    --amplicons amplicons.tsv

# 3. Or with Conda
nextflow run mnoguera/nf-codonyat \
    -profile conda \
    --samplesheet samples.csv \
    --reference reference.fasta \
    --amplicons amplicons.tsv
```

---

## Input Files

### Samplesheet (CSV)
```csv
sample,sam
sample1,/path/to/sample1.sam
sample2,/path/to/sample2.sam
```

### Reference FASTA
Header must contain protein annotations in the format:
```
>K03455|HIVHXB2CG PR(Protease):2253-2549;RT(Reverse Transcriptase):2550-3869;INT(Integrase):4230-5093
<sequence>
```

### Amplicons TSV
Tab-separated, 7 columns:
```
label   protein  reference  5p_seq  3p_seq  start  end
Amp_1   RT       ref        ATG     GCA     2550   2600
```

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--samplesheet` | *required* | CSV with `sample,sam` columns |
| `--reference` | *required* | Annotated reference FASTA |
| `--amplicons` | *required* | Amplicon definitions TSV |
| `--protein` | `RT` | Protein name to analyse |
| `--ratio_upper` | `3.162` | Strand ratio upper threshold (≈10× forward) |
| `--ratio_lower` | `0.316` | Strand ratio lower threshold (≈0.1× forward) |
| `--entropy_threshold` | `0.0` | Minimum Shannon entropy per position |
| `--outdir` | `results` | Output directory |
| `--publish_dir_mode` | `copy` | How to publish files (`copy`, `symlink`, `move`) |

---

## Output

```
results/
├── codonyat_summary.tsv          # Combined table from all samples
└── samples/
    ├── sample1/
    │   ├── sample1.tsv           # Per-codon variant frequencies
    │   └── sample1.xml           # Per-position diagnostics
    └── sample2/
        ├── sample2.tsv
        └── sample2.xml
```

---

## Documentation

Full documentation is available in the `docs/` directory:

- [Usage](docs/usage.md) — CLI reference and parameter descriptions
- [Output](docs/output.md) — Description of all output files

---

## Requirements

- Nextflow ≥ 22.x
- Java 11+
- Docker, Singularity, or Conda/Mamba

---

## Development

```bash
# Clone the pipeline
git clone https://github.com/mnoguera/nf-codonyat.git
cd nf-codonyat

# Lint
nextflow lint .

# Run locally with test data
nextflow run . -profile test -profile docker

# Run locally without any container
nextflow run . -profile test -profile conda
```

---

## License

MIT — see [LICENSE](LICENSE)
