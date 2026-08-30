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
| `VARIANT` | Codon-level variant (amino acid change, e.g. `M184V`) |
| `POSITION` | Codon position in the protein |
| `FREQ` | Variant frequency as a percentage of total depth |
| `FWCOV` | Forward-strand read count |
| `RVCOV` | Reverse-strand read count |
| `TOTALCOV` | Total coverage at this codon position |
| `RATIO` | Forward / reverse coverage ratio |

## Combined Summary (`codonyat_summary.tsv`)

Same columns as above, plus:

| Column | Description |
|--------|-------------|
| `SAMPLE` | Sample identifier (from samplesheet) |

## Diagnostics XML (`{sample}.xml`)

Per-position diagnostics in a `<SamContainer>` XML tree:

```xml
<SamContainer>
  <Position pos="184">
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
