# Influenza A test data

Research use only. Synthetic reads; not a clinical dataset.

Used by `-profile test_flua` (custom mode). Rebuild with
`assets/testdata/make_non_hiv_testdata.py`.

- HA, segment 4: NCBI RefSeq **NC_002017.1** (1,778 nt; CDS 33-1733).
- NA, segment 6: NCBI RefSeq **NC_002018.1** (1,413 nt; CDS 21-1385).
  NCBI places no extra restrictions on use; cite the accessions.
- Annotation: 4-column BED (`annotation.bed`) with those CDS.
- Primers: one synthetic pair per segment (`primers.bed`). Not a
  published scheme; it only exists so the pipeline can derive amplicons.
- Reads: synthetic 2x250 amplicon pairs (`FLU_SIM_R{1,2}.fastq.gz`),
  deterministic (gzip mtime=0). Names have no `_<digits>` suffix.
  Simulated codon changes are frequencies only: HA 5 L>V at 25.0 of HA
  coverage, NA 3 P>A at 60.0 of NA coverage. No interpretation.

Contamination is skipped (`--skip_contamination`); no influenza Kraken2
database is bundled.
