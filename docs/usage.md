# nf-codonyat — Usage

> Research use only: descriptive QC, contamination, subtype-estimate, consensus and frequency outputs;
> no drug-resistance or clinical interpretation.

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
| `--kraken2_db` | Kraken2 database folder; required when the samplesheet has FASTQ samples, unless `--skip_contamination` |

## Analysis Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--protein` | `all` | One protein (`RT`), a comma-separated list (`PR,RT,INT`) or `all` proteins annotated in the reference header. All requested proteins are counted in one codonyat pass. Use `--protein RT` to reproduce v0.2.0 outputs for SAM samples. |
| `--ratio_upper` | `3.162` | Upper strand ratio threshold |
| `--ratio_lower` | `0.316` | Lower strand ratio threshold |
| `--entropy_threshold` | `0.0` | Minimum Shannon entropy per position |

## Read Processing and Filtering Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--fastp_args` | `--qualified_quality_phred 20 --unqualified_percent_limit 40 --length_required 50 --cut_tail --cut_tail_mean_quality 20` | fastp options for FASTQ samples. `--detect_adapter_for_pe` is added automatically for paired-end reads. |
| `--merge_pairs` | `true` | Merge overlapping pairs with BBMerge (paired-end only). Merged reads are aligned as single-end, the pairs that did not merge as paired-end, in one Bowtie2 step; the two BAMs are merged. |
| `--bbmerge_args` | `''` | Extra BBMerge arguments (BBMerge defaults otherwise; `ordered=t` is always set so the read order, and therefore the output tables, are reproducible). |
| `--strand_metrics_unmerged` | `true` | Also align all trimmed pairs (before merging) as pairs and run codonyat on them; their FWCOV/RVCOV/RATIO are added as `*_UNMERGED` columns. Only for paired-end samples with `--merge_pairs`. |
| `--bowtie2_args` | `--very-sensitive-local` | Bowtie2 options for FASTQ samples (`--reorder` is always added). |
| `--min_mapq` | `20` | Minimum mapping quality (`samtools view -q`), applied to FASTQ **and** SAM samples |
| `--exclude_flags` | `0x904` | Alignments removed (`samtools view -F`): unmapped (0x4), secondary (0x100), supplementary (0x800) |

`codonyat` does no mapping-quality or flag filtering itself (it only skips unmapped reads), so this
filter is applied before it for every sample. Use `--min_mapq 0 --exclude_flags 0x4` to approximate the
old, unfiltered behaviour for SAM inputs.

With `--merge_pairs false`, paired-end samples are aligned as pairs exactly as in v0.2.0 and the strand
branch is not needed (with `--protein RT` the codon table is identical to v0.2.0's).

## Contamination Report (Kraken2)

| Flag | Default | Description |
|------|---------|-------------|
| `--kraken2_db` | — | Kraken2 database folder (`hash.k2d`, `opts.k2d`, `taxo.k2d`), e.g. Standard-8 |
| `--skip_contamination` | `false` | Skip the report |
| `--kraken2_confidence` | `0.0` | Kraken2 `--confidence` |
| `--kraken2_memory_mapping` | `false` | Kraken2 `--memory-mapping` (database read from disk instead of RAM) |
| `--contamination_warn_hiv_pct` | `50` | Warning when HIV-1 is below this % of classified fragments |
| `--contamination_warn_human_pct` | `50` | Warning when human reads exceed this % of all fragments |

The report runs on the trimmed reads and never removes reads or stops a sample.

Getting Standard-8 (about 5.5 GB download, about 8 GB RAM to run):

```bash
mkdir -p k2_standard_08
curl -L https://genome-idx.s3.amazonaws.com/kraken/k2_standard_08_GB_20260626.tar.gz | tar -xz -C k2_standard_08
```

Newer releases are listed at https://benlangmead.github.io/aws-indexes/k2.

## Subtype Estimate (BBSplit)

| Flag | Default | Description |
|------|---------|-------------|
| `--subtype_panel` | `assets/presets/hiv1_subtype_panel_v1` | Panel folder: one `<bin>.fa` per bin and `panel.tsv` (first column = bin; the first bin listed is BBSplit's primary reference) |
| `--skip_subtype` | `false` | Skip the estimate |
| `--subtype_min_reads` | `100` | Fewer reads assigned to the panel → `undetermined` |
| `--subtype_min_margin` | `10` | Margin (% points) between the top two bins below which the call is flagged `ambiguous_or_possible_recombinant` |

BBSplit maps the trimmed reads competitively to all panel references (`ambiguous2=toss`: reads that fit two
bins equally well are counted as ambiguous, not assigned). The estimate is the % of unambiguously assigned
reads per bin. It is a read-mapping based estimate for research use, not a genotyping result.

## Consensus (iVar)

| Flag | Default | Description |
|------|---------|-------------|
| `--skip_consensus` | `false` | Skip the consensus |
| `--consensus_threshold` | `0.5` | iVar `-t`: the consensus uses the fewest bases that together make up this fraction of the depth; an IUPAC code is written when more than one base is needed |
| `--consensus_min_depth` | `100` | iVar `-m`: positions below this depth are `N` |
| `--consensus_insertion_threshold` | `0.5` | iVar `-c`: insertions seen in at least this fraction of reads are added |
| `--consensus_min_bq` | `20` | iVar `-q`: minimum base quality |

The pileup is `samtools mpileup -aa -A -B -d 0 -Q 0` on the filtered alignments (all positions, orphan pairs
kept, no BAQ, no depth cap; base quality is applied by iVar). Majority deletions are applied, so the
consensus can be shorter than the reference; the indel table shows every indel at ≥ 5% and whether it is
in the consensus.

## Intermediate Files

| Flag | Default | Description |
|------|---------|-------------|
| `--save_intermediates` | `false` | Also publish trimmed FASTQ, the merged/not-merged part BAMs, the strand-branch BAM and codon table, raw iVar output and Kraken2 per-read assignments |

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

- `docker` — Docker: `ghcr.io/sjoclaudi/nf-codonyat:0.3.0` for codonyat and the helper scripts, BioContainers images for the nf-core modules (recommended)
- `singularity` — Singularity/Apptainer, same images
- `conda` — Conda environments (`modules/local/codonyat/run/environment.yml` and each nf-core module's own)
- `mamba` — same environment, created with mamba
- `test` — bundled test dataset: two synthetic SAM samples, one real FASTQ pair and a tiny Kraken2 database (combine with one of the above, e.g. `-profile test,docker`)
- `standard` — local execution; `codonyat-runner` must already be on your `PATH`

## Samplesheet

```csv
sample,fastq_1,fastq_2,sam
sampleA,sampleA_R1.fastq.gz,sampleA_R2.fastq.gz,
sampleB,sampleB.fastq.gz,,
sampleC,,,/data/run42/sampleC.sam
```

| Column | Description |
|--------|-------------|
| `sample` | Sample identifier (must be unique, no spaces) |
| `fastq_1` | Gzipped FASTQ, read 1 or single-end reads |
| `fastq_2` | Gzipped FASTQ, read 2 (leave empty for single-end) |
| `sam` | SAM file already aligned to `--reference` |

Each row needs either `fastq_1` or `sam`, not both. Relative paths are resolved against the folder that
contains the samplesheet. The original two-column `sample,sam` format is still accepted.

Only Illumina data (paired-end or single-end) is supported. The pipeline prints a warning when the first
read header of a FASTQ looks like Oxford Nanopore or Ion Torrent.

FASTQ samples go through FastQC (raw reads), fastp, Kraken2, the subtype estimate, BBMerge (paired-end)
and Bowtie2. Single-end samples skip BBMerge and the strand branch. SAM samples skip all of these steps.
All samples then go through the samtools filter above, codonyat, the amino-acid table, the consensus and MultiQC.

## Examples

### With Docker
```bash
nextflow run sjoclaudi/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --kraken2_db k2_standard_08 \
    --outdir my_results
```

### SAM inputs only, one protein (same codon tables as v0.2.0)
```bash
nextflow run sjoclaudi/nf-codonyat \
    -profile docker \
    --samplesheet sam_samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --protein RT
```

### With Conda
```bash
nextflow run sjoclaudi/nf-codonyat \
    -profile conda \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --kraken2_db k2_standard_08
```

### Custom thresholds
```bash
nextflow run sjoclaudi/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference ref.fasta \
    --amplicons amplicons.tsv \
    --kraken2_db k2_standard_08 \
    --protein PR,RT \
    --consensus_min_depth 50 \
    --ratio_upper 10.0 \
    --ratio_lower 0.1 \
    --entropy_threshold 0.5
```
