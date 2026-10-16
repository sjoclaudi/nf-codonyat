# SARS-CoV-2 test data

Research use only. Synthetic reads; not a clinical dataset.

## Custom-mode files (`-profile test_sarscov2`)

Unannotated MN908947.3 FASTA, GFF3 CDS, ARTIC nCoV-2019 V4.1 primer BED,
and synthetic 2x250 amplicon pairs (`SARS2_SIM_R{1,2}.fastq.gz`). Rebuild
with `assets/testdata/make_non_hiv_testdata.py`.

- Reference: NCBI Nucleotide **MN908947.3** (29,903 nt). NCBI places no
  extra restrictions on use; cite the accession.
- CDS: NCBI feature table for MN908947.3, written as GFF3 (11 CDS;
  ORF1ab is two CDS rows sharing `ID=cds-ORF1ab`).
- Primers: ARTIC nCoV-2019 V4.1
  (`nCoV-2019/V4.1/SARS-CoV-2.primer.bed`, CC BY 4.0). Please cite ARTIC
  if you use this scheme. Same coordinates as
  `assets/presets/sars-cov-2/primers.bed`.
- Reads: synthetic, deterministic (gzip mtime=0). Names have no
  `_<digits>` suffix. Simulated codon changes are frequencies only: S 614 D>G at
  70.0 of amplicon 78 coverage, N 203/204 at 40.0 of amplicon 96
  coverage. No interpretation.

Contamination is skipped (`--skip_contamination`); no SARS-CoV-2 Kraken2
database is bundled.

## Preset files (`--preset sars-cov-2`)

Synthetic Illumina-like paired-end reads (`SARS2_S_R{1,2}.fastq.gz`) from
MN908947.3 spike coordinates 21563-25384, used by the ARTIC preset
nf-test. Reference and primers come from `assets/presets/sars-cov-2/`
(see that folder's SOURCES.md).
