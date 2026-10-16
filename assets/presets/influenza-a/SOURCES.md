# Influenza A preset sources

Research use only.

## Reference

A/Puerto Rico/8/1934(H1N1) RefSeq segments (NCBI Nucleotide):

| Accession    | Segment | Proteins (codonyat header syntax) |
|--------------|---------|-----------------------------------|
| NC_002023.1  | 1 PB2   | PB2:28-2307 |
| NC_002021.1  | 2 PB1   | PB1:25-2298; PB1-F2:119-382 |
| NC_002022.1  | 3 PA    | PA:25-2175; PA-X:25-597,599-784 (frameshift) |
| NC_002017.1  | 4 HA    | HA:33-1733 |
| NC_002019.1  | 5 NP    | NP:46-1542 |
| NC_002018.1  | 6 NA    | NA:21-1385 |
| NC_002016.1  | 7 M     | M1:26-784; M2:26-51,740-1007 (spliced) |
| NC_002020.1  | 8 NS    | NS1:27-719; NEP:27-56,529-864 (spliced) |

Coordinates are NCBI GenBank CDS features. Multi-interval proteins use the
codonyat 1.2.0 comma syntax.

## Primers

**Unverified.** No primer scheme is bundled. Provide `--primer_bed` (6-column,
`_LEFT`/`_RIGHT`, chromosome IDs matching the FASTA record ids above) or
`--amplicons`. Do not invent primers.

## Taxonomy

- NCBI taxid **11320** (Influenza A virus)
