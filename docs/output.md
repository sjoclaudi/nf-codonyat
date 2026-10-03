# nf-codonyat — Output Description

## Directory Structure

```
results/
├── codonyat_summary.tsv          # Combined variant table (all samples)
├── samples/
│   ├── sample1/
│   │   ├── sample1.tsv           # Per-codon variant table
│   │   └── sample1.xml           # Per-position diagnostics
│   └── sample2/
│       ├── sample2.tsv
│       └── sample2.xml
└── pipeline_info/
    ├── execution_timeline.html
    ├── execution_report.html
    └── execution_trace.txt
```

## Per-Sample TSV (`{sample}.tsv`)

Columns:

| Column | Description |
|--------|-------------|
| `FILE` | Input SAM filename |
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
