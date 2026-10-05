# nf-codonyat

**Codon-aware amino acid variant typing of HIV-1 amplicon NGS data — Nextflow pipeline**

Wraps the [`codonyat`](https://github.com/mnoguera/codonyat) Python package in a Nextflow pipeline for viral amplicon NGS analysis.

> **Research use only.** The outputs are descriptive: QC, a contamination report, a read-mapping based
> subtype estimate, a consensus sequence, and codon and amino-acid frequency tables. The pipeline does
> no drug-resistance or clinical interpretation and is not a diagnostic tool.

---

## Overview

`nf-codonyat` takes Illumina FASTQ reads (paired-end or single-end) or already aligned SAM files, an annotated
reference FASTA and an amplicon definitions file. It produces per-codon frequency tables (TSV) and a per-position
XML file per sample for every annotated protein (one codonyat pass), amino-acid frequency tables, a consensus
sequence, a contamination report, a subtype estimate, provenance files and a MultiQC report.

```
FASTQ (Illumina PE/SE)
  │
  ├─► FastQC (raw reads)
  ▼
 [1] fastp ──► trimmed reads
  ├─► [2] Kraken2 ─► contamination report (+ warning flag; no reads removed)
  ├─► [3] BBSplit vs subtype panel (A / B / group M) ─► subtype estimate (% reads per bin)
  ▼
 [5] BBMerge (PE only) ─► merged reads (SE) + not-merged pairs (PE)
  ▼
 [4] Bowtie2 --very-sensitive-local (one pass) ─► samtools merge ─► sorted BAM ──┐
                                                                                ├─► samtools flagstat
SAM ────────────────────────────────────────────────────────────────────────────┘        │
                              samtools view -q 20 -F 0x904 ─► samtools flagstat ◄─────────┘
                                         │
                ├─► [6] iVar consensus (t 0.5, IUPAC, N < 100x) ─► consensus.fa + indel table
                └─► [7] codonyat (all proteins, one pass) ─► codon TSV/XML ─► amino-acid table

PE strand branch: all trimmed pairs (before merging) ─► Bowtie2 PE ─► filter ─► codonyat
                  ─► strand metrics (*_UNMERGED columns in the amino-acid table)
End: codonyat_summary.tsv, aa_variants_summary.tsv, consensus_all.fa, provenance, MultiQC
```

- **FastQC** runs on the raw reads; fastp's report covers the trimmed reads.
- **Kraken2** (step 2) and the **subtype estimate** (step 3) are report-only branches: they never remove reads or
  stop a sample. A warning flag is set when HIV-1 is below 50% of classified fragments or human reads exceed 50%.
- **BBMerge** merges overlapping pairs, so an overlapping fragment counts once per codon instead of twice.
  Merged reads (single-end) and the pairs that did not merge (paired-end) are aligned in one Bowtie2 step and
  combined into one sorted BAM.
- **Strand metrics:** a merged read is written in R1's orientation, so after merging FWCOV/RVCOV/RATIO describe
  fragment orientation. The pipeline therefore also aligns *all* trimmed pairs as ordinary pairs and reports their
  read-strand metrics next to the merged-read results (`--strand_metrics_unmerged`, PE only).
- **samtools view** keeps primary, mapped alignments with MAPQ ≥ 20 for FASTQ *and* SAM samples (codonyat does
  no quality filtering itself).
- **iVar consensus:** bases making up ≥ 50% of the depth (IUPAC code when more than one base is needed),
  N below 100x, majority insertions and deletions applied.
- **codonyat 1.1** streams the alignments (flat memory) and counts every requested protein in one pass.
- SAM samples skip every FASTQ-only step and give the same codon tables as v0.2.0 with the same `--protein`.
- There is no duplicate removal (amplicon reads share start positions) and no primer clipping yet (see below).

---

## Quick Start

```bash
# 1. Install Nextflow (>= 25.04)
curl -s https://get.nextflow.io | bash

# 2. Get a Kraken2 database for the contamination report (once; ~5.5 GB download, ~8 GB RAM to run)
#    Standard-8 from https://benlangmead.github.io/aws-indexes/k2
mkdir -p k2_standard_08 && curl -L https://genome-idx.s3.amazonaws.com/kraken/k2_standard_08_GB_20260626.tar.gz | tar -xz -C k2_standard_08
#    (check the page for the current release name; or skip this step with --skip_contamination)

# 3. Run with Docker
nextflow run sjoclaudi/nf-codonyat \
    -profile docker \
    --samplesheet samples.csv \
    --reference reference.fasta \
    --amplicons amplicons.tsv \
    --kraken2_db k2_standard_08

# Bundled test data (tiny Kraken2 database, no download)
nextflow run sjoclaudi/nf-codonyat -profile test,docker
```

---

## Input Files

### Samplesheet (CSV)
```csv
sample,fastq_1,fastq_2,sam
sampleA,sampleA_R1.fastq.gz,sampleA_R2.fastq.gz,
sampleB,sampleB.fastq.gz,,
sampleC,,,/data/aligned/sampleC.sam
```
Each row has **either** FASTQ (`fastq_1`, plus `fastq_2` for paired-end) **or** a `sam`, never both.
Relative paths are resolved against the samplesheet's folder. A sheet with only `sample,sam` columns
(the original format) still works. SAM files must be aligned to the `--reference` sequence.
FASTQ data must be Illumina; the pipeline warns when the first read header looks like another platform.

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

### Kraken2 database
Any Kraken2 database folder (`hash.k2d`, `opts.k2d`, `taxo.k2d`). Standard-8 (archaea, bacteria, viral,
plasmid, human, UniVec_Core; capped at 8 GB) is the intended default. Required for FASTQ samples unless
`--skip_contamination`. Its file checksums are recorded in `pipeline_info/provenance.json`.

### Subtype panel
`assets/presets/hiv1_subtype_panel_v1/` (default `--subtype_panel`): pol-region references in three bins,
A (A1), B and a group M consensus. See its `SOURCES.md` for accessions, sources and how it was built.
The estimate is the % of reads that map unambiguously to each bin. It is a read-mapping based estimate for
research use, not a genotyping result: other subtypes and recombinants are expected to fall into the M bin
or split between bins (flagged when the margin between the top two bins is below `--subtype_min_margin`).

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--samplesheet` | *required* | CSV with `sample,fastq_1,fastq_2,sam` columns |
| `--reference` | *required* | Annotated reference FASTA |
| `--amplicons` | *required* | Amplicon definitions TSV |
| `--protein` | `all` | One protein, a comma-separated list (`PR,RT,INT`) or `all` annotated proteins |
| `--ratio_upper` / `--ratio_lower` | `3.162` / `0.316` | codonyat strand ratio thresholds |
| `--entropy_threshold` | `0.0` | Minimum Shannon entropy per position |
| `--fastp_args` | `--qualified_quality_phred 20 --unqualified_percent_limit 40 --length_required 50 --cut_tail --cut_tail_mean_quality 20` | fastp options; `--detect_adapter_for_pe` is added for paired-end |
| `--kraken2_db` | — | Kraken2 database folder (required for FASTQ unless `--skip_contamination`) |
| `--skip_contamination` | `false` | Skip the Kraken2 report |
| `--kraken2_confidence` | `0.0` | Kraken2 `--confidence` |
| `--kraken2_memory_mapping` | `false` | Kraken2 `--memory-mapping` |
| `--contamination_warn_hiv_pct` / `--contamination_warn_human_pct` | `50` / `50` | Warning thresholds (report only) |
| `--subtype_panel` | bundled `hiv1_subtype_panel_v1` | Panel folder (`<bin>.fa` per bin + `panel.tsv`) |
| `--skip_subtype` | `false` | Skip the subtype estimate |
| `--subtype_min_reads` / `--subtype_min_margin` | `100` / `10` | Minimum assigned reads; minimum margin (% points) between the top two bins |
| `--merge_pairs` | `true` | Merge overlapping pairs with BBMerge (PE only) |
| `--bbmerge_args` | `''` | Extra BBMerge arguments |
| `--strand_metrics_unmerged` | `true` | Strand metrics from all pre-merge pairs (PE with `--merge_pairs`) |
| `--bowtie2_args` | `--very-sensitive-local` | Bowtie2 options (`--reorder` is always added) |
| `--min_mapq` | `20` | Minimum MAPQ kept (`samtools view -q`), all samples |
| `--exclude_flags` | `0x904` | Alignments dropped (`samtools view -F`): unmapped, secondary, supplementary |
| `--skip_consensus` | `false` | Skip the consensus sequence |
| `--consensus_threshold` | `0.5` | iVar `-t` |
| `--consensus_min_depth` | `100` | iVar `-m` (N below this depth) |
| `--consensus_insertion_threshold` | `0.5` | iVar `-c` |
| `--consensus_min_bq` | `20` | iVar `-q` |
| `--save_intermediates` | `false` | Also publish trimmed FASTQ, per-part BAMs, raw iVar output, Kraken2 per-read output |
| `--outdir` | `results` | Output directory |
| `--publish_dir_mode` | `copy` | How to publish files |

All parameters are also described in `nextflow_schema.json`.

---

## Output

```
results/
├── codonyat_summary.tsv               # codon table, all samples
├── samples/<s>/<s>.{tsv,xml}          # codonyat codon table and per-position XML
├── variants/<s>.aa_variants.tsv, aa_variants_summary.tsv          # amino-acid frequencies
├── consensus/<s>.consensus.fa, <s>.consensus_indels.tsv, <s>.consensus_stats.tsv,
│             consensus_all.fa, consensus_stats.tsv
├── contamination/<s>.kraken2.report.txt, <s>.contamination.tsv, contamination_summary.tsv
├── subtype/<s>.subtype.tsv, subtype_summary.tsv, bbsplit/<s>.stats.txt
├── merge/<s>.bbmerge.log, <s>_ihist.txt
├── strand/<s>.strand_metrics_unmerged.tsv, <s>.pairs.bowtie2.log
├── alignment/<s>.bam, <s>.{merged,unmerged}.bowtie2.log (PE) or <s>.bowtie2.log (SE), flagstat/
├── fastqc/  fastp/
├── multiqc/multiqc_report.html
└── pipeline_info/  software_versions.yml, provenance.json, methods.md, execution reports
```

See [docs/output.md](docs/output.md) for the columns of every table.

---

## Software

- **Local steps** (codonyat and the helper scripts in `bin/`, Python standard library only):
  container `ghcr.io/sjoclaudi/nf-codonyat:0.3.0` built from the `Dockerfile`, or the conda environment
  `modules/local/codonyat/run/environment.yml`.
  Both install `codonyat==1.1.0` from PyPI.
- **Third-party steps** use [nf-core modules](https://nf-co.re/modules) (`modules/nf-core/`, pinned in
  `modules.json`), each with its own BioContainers image and conda environment: FastQC 0.12.1, fastp 1.3.6,
  Kraken2 2.1.6, BBMap 39.18 (BBSplit, BBMerge), Bowtie2 2.5.4, samtools 1.21/1.24, iVar 1.4.4 and MultiQC 1.35.

Nothing is installed at run time beyond the container images or conda environments.

## Resources

Kraken2 with Standard-8 needs about 8 GB RAM (the process asks for 10 GB; use `--kraken2_memory_mapping`
on smaller machines). BBSplit and BBMerge ask for 4 GB each. codonyat 1.1 stays under ~120 MB for 1M
alignments. A 16 GB machine runs the full pipeline.

## Future options

- **Primer clipping** (e.g. `ivar trim` or `samtools ampliconclip` with a primer BED) is not done yet.
  Primer sequences at read ends reflect the primer, not the virus, so variants under primer sites
  should be read with care until this is added.

## Requirements

- Nextflow ≥ 25.04 (tested with 26.04.6)
- Java 17 or 21
- Docker, Singularity/Apptainer, or Conda/Mamba

---

## Development

```bash
git clone https://github.com/sjoclaudi/nf-codonyat.git
cd nf-codonyat

nextflow lint .                          # must be clean; CI enforces it
docker build -t ghcr.io/sjoclaudi/nf-codonyat:0.3.0 .   # task image (CI builds it for the docker tests)
nextflow run . -profile test,docker      # or test,conda
nf-test test --profile docker            # or --profile conda
```

Test data in `assets/testdata/`:

- `sample1.sam`, `sample2.sam`: synthetic HXB2 (K03455) RT amplicon reads with known mutations
  spiked in (M41L, K65R, M184V and a T69 deletion; `make_testdata.py`).
- `consensus_rules.sam`: synthetic reads for the consensus rules (a mixture → IUPAC code, a majority
  3-bp deletion, a region below 100x; `make_consensus_testdata.py`).
- `HVG286PL_R1/R2.fastq.gz`: 2,000 read pairs randomly subsampled (`seqtk sample -s42`) from a
  real HIV-1 pol amplicon library (HVG286PL), used for the FASTQ path. `amplicons.tsv` has an
  `Amp_RT` row covering the whole RT coding region (HXB2 2550–3869) for it.
- `kraken2_tiny_db/`: a ~110 KB Kraken2 database with HXB2, phiX and the human mitochondrial genome
  (`make_kraken2_tiny_db.sh`), so tests need no database download.
- `reference.fasta`: annotated HXB2 (K03455), used by both paths.

---

## License

MIT — see [LICENSE](LICENSE)
