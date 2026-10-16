# HBV preset sources

Research use only.

## Reference

- Accession: **NC_003977.2** (Hepatitis B virus strain ayw, 3182 bp, circular)
- Source: NCBI Nucleotide / RefSeq
- Origin-crossing proteins are two intervals (codonyat 1.2.0 comma syntax),
  e.g. polymerase `P:2309-3182,1-1625` and large envelope
  `L:2850-3182,1-837`.
- Names are unique (`P`, `L`, `PreS2`, `S`, `X`, `preC`, `C`) because protein
  names cannot be repeated on one record.

## Primers

**Unverified.** No primer scheme is bundled. Provide `--primer_bed` or
`--amplicons`. Do not invent primers.

Minus-strand genes are not supported.

## Taxonomy

- NCBI taxid **10407** (Hepatitis B virus)
