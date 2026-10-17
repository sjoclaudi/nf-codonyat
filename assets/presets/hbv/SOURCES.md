# HBV preset sources

Research use only.

## Reference

- Accession: **X02763** (NCBI X02763.1, Hepatitis B virus serotype adw2, 3221 bp, circular)
- Source: NCBI Nucleotide. The scheme FASTA is a circular permutation of
  X02763.1 (scheme origin = NCBI base 1410); the bundled sequence is NCBI
  X02763.1 rotated to that origin so primer coordinates match.
- Origin-crossing proteins are two intervals (codonyat 1.2.0 comma syntax):
  polymerase `P:2307-3221,1-1623`, large envelope `L:2854-3221,1-835`, and
  middle envelope `PreS2:3211-3221,1-835`.
- Nested genes use unique names (`P`, `L`, `PreS2`, `S`, `X`, `preC`, `C`)
  because protein names cannot be repeated on one record. NCBI annotates L/C/P/X;
  PreS2, S and preC are the standard nested reading frames on those CDS.

## Primer scheme

- **quick-lab `hbv/600/v2.1.0`** 6-column BED derived from
  https://github.com/quick-lab/primerschemes
  (`primerschemes/hbv/600/v2.1.0/primer.bed`).
- Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
- Citation: Quick Lab primer schemes
  (https://github.com/quick-lab/primerschemes). Please cite the scheme if you
  use this preset.
- Numbered alt primers (`*_LEFT_N` / `*_RIGHT_N`) are collapsed to one `_LEFT`
  and one `_RIGHT` per amplicon (lowest index), as required by nf-codonyat.
- Unpaired LEFT-only spike-in primers (`de464cad_3`, `de464cad_4`, `de464cad_5`)
  are omitted because each amplicon must have exactly one `_LEFT` and one
  `_RIGHT`.
- One amplicon (`f3d7635a_5`) crosses the circular origin (LEFT near the end,
  RIGHT near the start).
- The seventh sequence column of the upstream ARTIC BED is dropped; primer
  sequences are taken from the reference at the BED coordinates.

Minus-strand genes are not supported.

## Taxonomy

- NCBI taxid **10407** (Hepatitis B virus)
