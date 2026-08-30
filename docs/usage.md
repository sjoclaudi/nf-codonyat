# nf-codonyat — Usage

## Command Line

```bash
nextflow run mnoguera/nf-codonyat [options]
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

## Output Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--outdir` | `results` | Output directory |
| `--publish_dir_mode` | `copy` | Publish mode: `copy`, `symlink`, or `move` |

## Profiles

Use `-profile` to select an execution environment:

- `docker` — Docker container (recommended)
- `singularity` — Singularity container
- `conda` — Conda/mamba environment
- `standard` — local execution (no container)

## Examples

### With Docker
```bash
nextflow run mnoguera/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --outdir my_results
```

### With Conda
```bash
nextflow run mnoguera/nf-codonyat \
    -profile conda \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv
```

### Custom thresholds
```bash
nextflow run mnoguera/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --protein PR \
    --ratio_upper 10.0 \
    --ratio_lower 0.1 \
    --entropy_threshold 0.5
```
