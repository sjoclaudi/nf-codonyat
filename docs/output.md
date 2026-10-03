# nf-codonyat — Output Description

## Directory Structure

```
results/
├── codonyat_summary.tsv          # Combined variant table (all samples)
├── samples/
│   └── <sample>/
│       ├── <sample>.tsv          # Per-codon variant table
│       └── <sample>.xml          # Per-position diagnostics
├── fastqc/                       # FASTQ samples only
│   ├── <sample>_1_fastqc.html    # FastQC on the raw reads (_1/_2 for paired-end)
│   └── <sample>_1_fastqc.zip
├── fastp/                        # FASTQ samples only
│   ├── <sample>.fastp.html       # Trimming/filtering report (before and after)
│   ├── <sample>.fastp.json
│   └── <sample>.fastp.log
├── alignment/
│   ├── <sample>.bam              # bowtie2 alignment, coordinate-sorted (FASTQ samples)
│   ├── <sample>.bowtie2.log      # bowtie2 alignment summary
│   └── flagstat/                 # all samples
│       ├── <sample>.aligned.flagstat    # before the MAPQ/flag filter
│       └── <sample>.filtered.flagstat   # after it (what codonyat sees)
├── multiqc/
│   ├── multiqc_report.html       # FastQC, fastp, bowtie2 and flagstat in one report
│   └── multiqc_report_data/
└── pipeline_info/
    ├── execution_timeline.html
    ├── execution_report.html
    ├── execution_trace.txt
    └── pipeline_dag.html
```

The filtered alignments passed to codonyat are not published (they are the BAM/SAM above minus reads
with MAPQ < `--min_mapq` and flags in `--exclude_flags`); the two flagstat files show what was removed.

## Per-Sample TSV (`{sample}.tsv`)

Columns:

| Column | Description |
|--------|-------------|
| `FILE` | Alignment file name codonyat read (always `<sample>.sam`) |
| `REFERENCE` | Reference sequence ID |
| `PROTEIN` | Protein name (from `--protein`) |
| `VARIANT` | Observed codon (e.g. `GTG`; `---` for a codon deletion) |
| `POSITION` | Reference coordinate of the codon's first base (e.g. HXB2 `3099` = RT codon 184) |
| `FREQ` | Variant frequency as a percentage of total depth |
| `FWCOV` | Forward-strand depth at this codon |
| `RVCOV` | Reverse-strand depth at this codon |
| `TOTALCOV` | Total coverage at this codon position |
| `RATIO` | Forward / reverse depth ratio at this codon |

## Combined Summary (`codonyat_summary.tsv`)

Same columns as above, plus:

| Column | Description |
|--------|-------------|
| `SAMPLE` | Sample identifier (from the samplesheet) |

## Diagnostics XML (`{sample}.xml`)

Per-position diagnostics in a `<SamContainer>` XML tree:

```xml
<SamContainer sample="sample1.sam" reference="K03455|HIVHXB2CG">
  <Position index="3099">
    <Depth>150</Depth>
    <FwCover>78</FwCover>
    <RvCover>72</RvCover>
    <Variants>
      <Variant codon="ATG" count="3" fw_reads="2" rv_reads="1"/>
      <Variant codon="GTG" count="147" fw_reads="76" rv_reads="71"/>
    </Variants>
  </Position>
</SamContainer>
```
