# RSV preset sources

Research use only.

## Reference

Multi-record FASTA so BED chromosome names match both subgroups:

| Accession | Subgroup | Proteins (codonyat header syntax) |
|-----------|----------|-----------------------------------|
| **NC_038235.1** | RSV-A (Human respiratory syncytial virus isolate HRSV/A/USA/001/198X) | NS1:99-518; NS2:628-1002; N:1140-2315; P:2346-3071; M:3261-4031; SH:4303-4497; G:4688-5584; F:5661-7385; M2-1:7606-8190; M2-2:8159-8431; L:8498-14995 |
| **NC_001781.1** | RSV-B (Human orthopneumovirus subgroup B) | NS1:99-518; NS2:626-1000; N:1140-2315; P:2348-3073; M:3263-4033; SH:4303-4500; G:4690-5589; F:5666-7390; M2-1:7618-8205; M2-2:8171-8443; L:8509-15009 |

Source: NCBI Nucleotide / RefSeq. Sequences are identical to the scheme
`reference.fasta`. Protein coordinates are NCBI GenBank CDS features. M2-1 and
M2-2 overlap (unique names; protein names cannot be repeated on one record).

## Primer scheme

- **quick-lab `rsva-rsvb/1000/v1.0.0`** 6-column BED derived from
  https://github.com/quick-lab/primerschemes
  (`primerschemes/rsva-rsvb/1000/v1.0.0/primer.bed`).
- Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
- Scheme status in `info.json`: **tested**.
- Citation: Quick Lab primer schemes
  (https://github.com/quick-lab/primerschemes). Please cite the scheme if you
  use this preset.
- Numbered alt primers (`*_LEFT_N` / `*_RIGHT_N`) are collapsed to one `_LEFT`
  and one `_RIGHT` per amplicon (lowest index), as required by nf-codonyat.
- The seventh sequence column of the upstream ARTIC BED is dropped; primer
  sequences are taken from the reference at the BED coordinates.

## Taxonomy

- NCBI taxid **11259** (Human orthopneumovirus / human RSV)
