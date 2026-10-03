# nf-codonyat

**Codon-aware amino acid variant typing — Nextflow pipeline**

Wraps the [`codonyat`](https://github.com/mnoguera/codonyat) Python package in a Nextflow pipeline for viral amplicon NGS analysis.

---

## Overview

`nf-codonyat` takes raw FASTQ reads or already aligned SAM files, an annotated reference FASTA and an amplicon definitions file, and produces per-codon variant frequency tables (TSV), a diagnostics file (XML) per sample, a combined summary and a MultiQC report.

```
FASTQ ─► FastQC (raw reads) ─► fastp ─► bowtie2 --very-sensitive-local ─► sorted BAM ─┐
                                                                                      ├─► samtools flagstat
SAM ──────────────────────────────────────────────────────────────────────────────────┘        │
                                         samtools view -q 20 -F 0x904 ◄────────────────────────┘
                                                    │
                                 samtools flagstat ◄┤
                                                    ▼
                                         codonyat-runner ─► per-sample TSV/XML ─► codonyat_summary.tsv
MultiQC: FastQC + fastp + bowtie2 + flagstat
```

- **FastQC** runs on the raw reads only; fastp's own report covers the trimmed reads.
- **fastp** trims and filters reads. Read pairs are never merged, because codonyat counts forward and reverse strand coverage separately.
- **bowtie2** aligns to the same reference FASTA used by codonyat (the index is built by the pipeline).
- **samtools view** keeps primary, mapped alignments with MAPQ ≥ 20, for FASTQ *and* SAM samples. `codonyat` 1.0.1 itself does no quality filtering (it only skips unmapped reads).
- There is no duplicate removal: in amplicon data every read in an amplicon starts at the same position, so position-based deduplication would discard real coverage.

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
sample,fastq_1,fastq_2,sam
patientA,patientA_R1.fastq.gz,patientA_R2.fastq.gz,
patientB,patientB.fastq.gz,,
patientC,,,/data/aligned/patientC.sam
```
Each row has **either** FASTQ (`fastq_1`, plus `fastq_2` for paired-end) **or** a `sam`, never both.
Relative paths are resolved against the samplesheet's folder. A sheet with only `sample,sam` columns
(the original format) still works. SAM files must be aligned to the `--reference` sequence.

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
| `--samplesheet` | *required* | CSV with `sample,fastq_1,fastq_2,sam` columns |
| `--reference` | *required* | Annotated reference FASTA |
| `--amplicons` | *required* | Amplicon definitions TSV |
| `--protein` | `RT` | Protein name to analyse |
| `--ratio_upper` | `3.162` | Strand ratio upper threshold (≈10× forward) |
| `--ratio_lower` | `0.316` | Strand ratio lower threshold (≈0.1× forward) |
| `--entropy_threshold` | `0.0` | Minimum Shannon entropy per position |
| `--fastp_args` | `--qualified_quality_phred 20 --unqualified_percent_limit 40 --length_required 50 --cut_tail --cut_tail_mean_quality 20` | fastp options (FASTQ samples); `--detect_adapter_for_pe` is added for paired-end |
| `--bowtie2_args` | `--very-sensitive-local` | bowtie2 options (FASTQ samples) |
| `--min_mapq` | `20` | Minimum mapping quality kept (`samtools view -q`), all samples |
| `--exclude_flags` | `0x904` | Alignments dropped (`samtools view -F`): unmapped, secondary, supplementary |
| `--outdir` | `results` | Output directory |
| `--publish_dir_mode` | `copy` | How to publish files (`copy`, `symlink`, `move`) |

---

## Output

```
results/
├── codonyat_summary.tsv          # Combined table from all samples
├── samples/<sample>/
│   ├── <sample>.tsv              # Per-codon variant frequencies
│   └── <sample>.xml              # Per-position diagnostics
├── fastqc/                       # FastQC on raw reads (FASTQ samples)
├── fastp/                        # fastp JSON/HTML reports and logs
├── alignment/
│   ├── <sample>.bam              # bowtie2 alignment, sorted (FASTQ samples)
│   ├── <sample>.bowtie2.log
│   └── flagstat/                 # <sample>.aligned / <sample>.filtered flagstat (all samples)
├── multiqc/multiqc_report.html
└── pipeline_info/                # Nextflow execution report, timeline, trace, DAG
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
- **Conda:** `modules/local/codonyat/run/environment.yml` (conda-forge Python + Biopython, `codonyat` via pip).

The read-processing steps use [nf-core modules](https://nf-co.re/modules) (`modules/nf-core/`, tracked in
`modules.json`), each with its own BioContainers image and conda environment: FastQC 0.12.1, fastp 1.3.6,
bowtie2 2.5.4, samtools 1.21/1.24 and MultiQC 1.35. Update them with `nf-core modules update`.

Nothing is installed at run time.

## Future options

- **Primer clipping** (e.g. `ivar trim` or `samtools ampliconclip` with a primer BED) is not done yet.
  Primer sequences at read ends reflect the primer, not the virus, so variants under primer sites
  should be read with care until this is added.

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

Test data in `assets/testdata/`:

- `sample1.sam`, `sample2.sam`: synthetic HXB2 (K03455) RT amplicon reads with known mutations
  spiked in (M41L, K65R, M184V and a T69 deletion). Regenerate them with `python3 make_testdata.py`
  inside that folder.
- `HVG286PL_R1/R2.fastq.gz`: 2,000 read pairs randomly subsampled (`seqtk sample -s42`) from a
  real HIV-1 pol amplicon library (HVG286PL), used for the FASTQ path. `amplicons.tsv` has an
  `Amp_RT` row covering the whole RT coding region (HXB2 2550–3869) for it.
- `reference.fasta`: annotated HXB2 (K03455), used by both paths.

---

## License

MIT — see [LICENSE](LICENSE)
