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

- `docker` — Docker, using `ghcr.io/sjoclaudi/nf-codonyat:0.1.0` (recommended)
- `singularity` — Singularity/Apptainer, same image
- `conda` — Conda environment from `modules/codonyat/run/environment.yml`
- `mamba` — same environment, created with mamba
- `test` — bundled two-sample test dataset (combine with one of the above, e.g. `-profile test,docker`)
- `standard` — local execution; `codonyat-runner` must already be on your `PATH`

## Samplesheet

```csv
sample,sam
sample1,sample1.sam
sample2,/data/run42/sample2.sam
```

Relative SAM paths are resolved against the folder that contains the samplesheet.

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
