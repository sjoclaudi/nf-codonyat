# Influenza B preset sources

Research use only.

## Reference

B/Lee/1940 RefSeq segments (NCBI Nucleotide). Record order follows the
NC_002204–NC_002211 accession series. Influenza B historically numbers RNA 1 as
PB1 and RNA 2 as PB2 (the opposite of influenza A); gene names below are the
RefSeq CDS `/gene` values.

| Accession    | RefSeq title | Proteins (codonyat header syntax) |
|--------------|--------------|-----------------------------------|
| NC_002204.1  | RNA 1        | PB1:21-2279 |
| NC_002205.1  | segment 2    | PB2:1-2313 |
| NC_002206.1  | segment 3    | PA:1-2181 |
| NC_002207.1  | segment 4    | HA:34-1788 |
| NC_002208.1  | segment 5    | NP:58-1740 |
| NC_002209.1  | segment 6    | NB:47-349; NA:54-1454 |
| NC_002210.1  | segment 7    | M1:25-771; BM2:771-1100 (overlapping stop/start) |
| NC_002211.1  | segment 8    | NS1:43-888; NEP:43-75,731-1066 (spliced) |

Coordinates are NCBI GenBank CDS features except BM2, which is the overlapping
ORF on NC_002210.1 (not a separate CDS in that RefSeq record). Multi-interval
proteins use the codonyat 1.2.0 comma syntax.

## Primers

No tiled public scheme is bundled. Full-segment amplification of influenza B is
commonly done with the universal IBV primers of Zhou et al. 2014
(https://pubmed.ncbi.nlm.nih.gov/24501036/). The preset runs with no primer
trimming by default (`requires_primer_bed: false`) and still accepts an optional
user `--primer_bed`.

## Taxonomy

- NCBI taxid **11520** (Influenza B virus)
