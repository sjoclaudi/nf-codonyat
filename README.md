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
nextflow run sjoclaudi/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference reference.fasta \
    --amplicons amplicons.tsv

# 3. Or with Conda
nextflow run sjoclaudi/nf-codonyat \
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
sample2,sample2.sam
```
Relative SAM paths are resolved against the samplesheet's folder.

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
Amp_1   RT       K03455|HIVHXB2CG  CCCATTAGCCCTATTGAGAC  AAGTTCTCTGAAATCTACTA  2550  2789
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

## Software

`codonyat` 1.0.1 (from PyPI) and Biopython 1.85 are provided in one of two ways:

- **Container:** `ghcr.io/sjoclaudi/nf-codonyat:0.1.0`, built from the `Dockerfile` in this repo and published by CI on every push to `main`.
- **Conda:** `modules/codonyat/run/environment.yml` (conda-forge Python + Biopython, `codonyat` via pip).

Nothing is installed at run time.

## Requirements

- Nextflow ≥ 25.04 (tested with 26.04)
- Java 17 or 21
- Docker, Singularity/Apptainer, or Conda/Mamba

---

## Development

```bash
git clone https://github.com/sjoclaudi/nf-codonyat.git
cd nf-codonyat

# Lint (must be clean; CI enforces it)
nextflow lint .

# Test run on the bundled data
nextflow run . -profile test,docker      # or test,conda

# nf-test (pipeline-level tests + output snapshot)
nf-test test --profile docker            # or --profile conda

# Build the task image locally (CI does this for the docker tests)
docker build -t ghcr.io/sjoclaudi/nf-codonyat:0.1.0 .
```

The test data in `assets/testdata/` is synthetic: HXB2 (K03455) RT amplicons with
known mutations spiked in (M41L, K65R, M184V and a T69 deletion). Regenerate it with
`python3 make_testdata.py` inside that folder.

---

## License

MIT — see [LICENSE](LICENSE)
