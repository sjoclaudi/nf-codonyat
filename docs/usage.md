# nf-codonyat — Usage

## Command Line

```bash
nextflow run sjoclaudi/nf-codonyat [options]
```

## Required Parameters

| Flag | Description |
|------|-------------|
| `--samplesheet` | Path to samplesheet CSV |
| `--reference` | Path to annotated reference FASTA |
| `--amplicons` | Path to amplicon definitions TSV |

## Analysis Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--protein` | `RT` | Protein to analyse |
| `--ratio_upper` | `3.162` | Upper strand ratio threshold |
| `--ratio_lower` | `0.316` | Lower strand ratio threshold |
| `--entropy_threshold` | `0.0` | Minimum Shannon entropy per position |

## Read Processing and Filtering Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--fastp_args` | `--qualified_quality_phred 20 --unqualified_percent_limit 40 --length_required 50 --cut_tail --cut_tail_mean_quality 20` | fastp options for FASTQ samples. `--detect_adapter_for_pe` is added automatically for paired-end reads. Read pairs are never merged. |
| `--bowtie2_args` | `--very-sensitive-local` | bowtie2 options for FASTQ samples |
| `--min_mapq` | `20` | Minimum mapping quality (`samtools view -q`), applied to FASTQ **and** SAM samples |
| `--exclude_flags` | `0x904` | Alignments removed (`samtools view -F`): unmapped (0x4), secondary (0x100), supplementary (0x800) |

`codonyat` 1.0.1 does no mapping-quality or flag filtering itself (it only skips unmapped reads), so this
filter is applied before it for every sample. Use `--min_mapq 0 --exclude_flags 0x4` to approximate the
old, unfiltered behaviour for SAM inputs.

## Output Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--outdir` | `results` | Output directory |
| `--publish_dir_mode` | `copy` | Publish mode: `copy`, `symlink`, or `move` |

Set `--outdir` on the command line or in a `-params-file`, not in a config file passed with `-c`.
Nextflow reads `-c` files after the pipeline config has already placed the execution reports
(`<outdir>/pipeline_info/`). If a `-c` file changes `outdir`, the run continues and results go to the
new folder, but the reports stay in the earlier `pipeline_info` folder (the profile's or the default
`results/pipeline_info`); the pipeline prints a warning saying where they went.

## Profiles

Use `-profile` to select an execution environment:

- `docker` — Docker: `ghcr.io/sjoclaudi/nf-codonyat:0.1.0` for codonyat, BioContainers images for the nf-core modules (recommended)
- `singularity` — Singularity/Apptainer, same images
- `conda` — Conda environments (`modules/local/codonyat/run/environment.yml` and each nf-core module's own)
- `mamba` — same environment, created with mamba
- `test` — bundled test dataset: two synthetic SAM samples and one real FASTQ pair (combine with one of the above, e.g. `-profile test,docker`)
- `standard` — local execution; `codonyat-runner` must already be on your `PATH`

## Samplesheet

```csv
sample,fastq_1,fastq_2,sam
patientA,patientA_R1.fastq.gz,patientA_R2.fastq.gz,
patientB,patientB.fastq.gz,,
patientC,,,/data/run42/patientC.sam
```

| Column | Description |
|--------|-------------|
| `sample` | Sample identifier (must be unique, no spaces) |
| `fastq_1` | Gzipped FASTQ, read 1 or single-end reads |
| `fastq_2` | Gzipped FASTQ, read 2 (leave empty for single-end) |
| `sam` | SAM file already aligned to `--reference` |

Each row needs either `fastq_1` or `sam`, not both. Relative paths are resolved against the folder that
contains the samplesheet. The original two-column `sample,sam` format is still accepted.

FASTQ samples go through FastQC (raw reads), fastp and bowtie2. SAM samples skip those steps. Both then go
through the samtools filter above, codonyat and MultiQC.

## Examples

### With Docker
```bash
nextflow run sjoclaudi/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --outdir my_results
```

### With Conda
```bash
nextflow run sjoclaudi/nf-codonyat \
    -profile conda \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv
```

### Custom thresholds
```bash
nextflow run sjoclaudi/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --protein PR \
    --ratio_upper 10.0 \
    --ratio_lower 0.1 \
    --entropy_threshold 0.5
```
