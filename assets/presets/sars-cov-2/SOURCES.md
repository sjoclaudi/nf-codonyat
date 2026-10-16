# SARS-CoV-2 preset sources

Research use only.

## Reference

- Accession: **MN908947.3** (Wuhan-Hu-1, complete genome)
- Source: NCBI Nucleotide
- Protein coordinates: NCBI GenBank CDS features on MN908947.3
- ORF1ab uses the −1 ribosomal frameshift as two intervals
  `266-13468,13468-21555` (base 13468 read twice), per the GenBank `join()` and
  the codonyat 1.2.0 comma-interval syntax.

## Primer scheme

- **ARTIC nCoV-2019 / SARS-CoV-2 V4.1** 6-column BED derived from
  https://github.com/artic-network/primer-schemes
  (`nCoV-2019/V4.1/SARS-CoV-2.primer.bed`).
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0).
- Citation: ARTIC Network primer schemes
  (https://github.com/artic-network/primer-schemes). Please cite ARTIC if you
  use this preset.
- Alt primers (`*_LEFT_alt*`) are omitted so each amplicon has exactly one
  `_LEFT` and one `_RIGHT` primer as required by nf-codonyat.
- The seventh sequence column of the upstream ARTIC BED is dropped; primer
  sequences are taken from the reference at the BED coordinates.

## Taxonomy

- NCBI taxid **2697049** (Severe acute respiratory syndrome coronavirus 2)
