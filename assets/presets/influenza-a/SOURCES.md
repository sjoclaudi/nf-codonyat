# Influenza A preset sources

Research use only.

## Reference

The bundled FASTA uses the **artic-flu-a/800/v1.0.0** scheme record IDs so primer
BED chromosome names match. Five segments are A/California/07/2009(H1N1) RefSeq
(NCBI Nucleotide), identical to the scheme FASTA. The three polymerase records
keep the scheme names (not NC_026435.1 / NC_026437.1 / NC_026438.1) because the
scheme sequences are A/chicken/Germany/1934 and A/chicken/Rostock/45/1934 CDS
substrings, not the 2009 polymerase segments.

| Record ID (BED chrom) | Segment | NCBI source | Proteins (codonyat header syntax) |
|-----------------------|---------|-------------|-----------------------------------|
| `pb2_1934_Avian_A_chicken_Rostock_45_1934_Germany_H7N1` | 1 PB2 | CY077417.1 CDS 28-2307 plus 3′ UTR | PB2:1-2280 |
| `pb1_1934_Avian_A_chicken_Germany_1934_Germany_H7N1` | 2 PB1 | GU052952.1 CDS 13-2286 plus 3′ UTR | PB1:1-2274; PB1-F2:95-358 |
| `pa_1934_Avian_A_chicken_Germany_1934_Germany_H7N1` | 3 PA | GU052951.1 CDS 13-2163 plus 3′ UTR | PA:1-2151; PA-X:1-570,572-760 (frameshift, 252 aa plus stop) |
| NC_026433.1 | 4 HA | NCBI RefSeq | HA:1-1701 |
| NC_026436.1 | 5 NP | NCBI RefSeq | NP:1-1497 |
| NC_026434.1 | 6 NA | NCBI RefSeq | NA:1-1410 |
| NC_026431.1 | 7 M | NCBI RefSeq | M1:1-759; M2:1-26,715-982 (spliced) |
| NC_026432.1 | 8 NS | NCBI RefSeq | NS1:1-660; NEP:1-30,503-838 (spliced) |

The polymerase scheme FASTA entries are CDS-only (no UTRs). Universal 3′ primers
in the scheme BED end 11 bp past those CDS. The 3′ UTR from the NCBI parent
record is appended so primer coordinates stay in range; 5′ coordinates are
unchanged. Coordinates are NCBI GenBank CDS features mapped onto those
sequences. Multi-interval proteins use the codonyat 1.2.0 comma syntax.

Those three polymerase records are the 1934 avian sequences used by the ARTIC
`artic-flu-a` scheme, not the 2009 CA/07 polymerase segments. Modern samples
will show lineage differences on PB2, PB1 and PA.

## Sequence edits

The artic-flu-a scheme FASTA (and RefSeq NC_026433.1 / NC_026436.1) keep IUPAC
`R` at three sites. Each was resolved to a single base so the reference amino
acid is not `X`. The scheme FASTA still has `R` at these positions.

| Record | Position | Scheme / RefSeq | Resolved | Source |
|--------|----------|-----------------|----------|--------|
| NC_026433.1 (HA) | 716 | R | A | Majority of CA/07/2009 GenBank CDS (FJ966974.1, FJ981613.1, KC781785.1, KF009554.1, KU933485.1) |
| NC_026433.1 (HA) | 719 | R | A | Same majority (`CAA`); CY121680.1 has G |
| NC_026436.1 (NP) | 341 | R | A | Majority of CA/07/2009 GenBank CDS (GQ338390.1, KU933486.1, CY121683.1); FJ969536.1 (RefSeq source) still has R |

## Primer scheme

- **quick-lab / ARTIC `artic-flu-a/800/v1.0.0`** 6-column BED derived from
  https://github.com/quick-lab/primerschemes
  (`primerschemes/artic-flu-a/800/v1.0.0/primer.bed`).
- Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
- Scheme status in `info.json`: **draft**.
- Citation: Quick Lab primer schemes
  (https://github.com/quick-lab/primerschemes). Please cite the scheme if you
  use this preset.
- Numbered alt primers (`*_LEFT_N` / `*_RIGHT_N`) are collapsed to one `_LEFT`
  and one `_RIGHT` per amplicon (lowest index), as required by nf-codonyat.
- The seventh sequence column of the upstream ARTIC BED is dropped; primer
  sequences are taken from the reference at the BED coordinates.

## Taxonomy

- NCBI taxid **11320** (Influenza A virus)
