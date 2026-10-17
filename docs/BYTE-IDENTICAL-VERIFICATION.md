# Byte-identical verification

Research use only.

## v0.7.0 research flags (defaults)

`codonyat-runner --help` (1.3.1): `--min-freq`, `--min-coverage` and `--sb-alpha` only set the
stats / AAVF FILTER floors (defaults 0.01 / 10 / 0.05). They do not change codon TSV/XML.
`--min-baseq` is off when omitted; when set it filters counted codons.

nf-codonyat therefore:

- does not pass `--min-baseq` when `params.min_baseq` is null (the default)
- passes `--min-freq` / `--min-coverage` / `--sb-alpha` only when `--emit_stats` or `--emit_aavf` is on
- never passes `--collapsed-read-counts`

So the default hiv1 (`-profile test`), `test_sarscov2` and `test_flua` runner command is
unchanged, and those profiles' codon TSV/XML stay byte-identical. Proof (no Docker):
`python3 tests/test_codonyat_research_flags.py` runs the 1.3.1 runner on the hiv1 testdata SAM
and on references/amplicons prepared like `test_sarscov2` / `test_flua`; TSV/XML MD5s match
with and without the default extra flags. `--min-baseq 60` changes the hiv1 table (testdata
qualities are Phred 40).


## v0.5.0 vs v0.4.0 (HIV-1)

HIV-1 analysis tables must match v0.4.0 except:

- contamination tables **append** `TARGET_TAXID`, `TARGET_READS`, `TARGET_PCT` (`HIV1_*` values unchanged)
- new files: `reference/{validation.json,annotation_used.tsv,amplicons_used.tsv,reference_used.fasta}` and `pipeline_info/run_mode.json`
- provenance / timestamps / `software_versions.yml` (`codonyat: "1.2.1"`) / pipeline version
- two extra processes (`PREPARE_REFERENCE`, `CHECK_VALIDATION`) so the HIV-1 test graph is 46 succeeded tasks (was 44)

A full side-by-side `-profile test,docker` diff against a v0.4.0 outdir was **not** re-run in this
environment (no Nextflow on the agent). CI on this branch is the check: existing codon / amino-acid /
consensus / subtype snapshots stay pinned; the contamination snapshot is dropped because of the appended
columns.

## v0.4.0 vs v0.3.1 (`9b11f81`)

This documents a real run of `-profile test,docker` on
`main@9b11f81` and on the 0.4.0 branch, into separate outdirs, then a recursive
diff of the published results.

## Commands (2026-10-05, Europe/Madrid)

```bash
# Image used by the pipeline (codonyat 1.1.0 from PyPI)
docker build --network host -t ghcr.io/sjoclaudi/nf-codonyat:0.3.0 .

# Baseline (main @ 9b11f81)
git worktree add /workspace/nfc-main 9b11f81
cd /workspace/nfc-main
source ~/.nfenv
nextflow run . -profile test,docker \
  --outdir /workspace/nfc-verify/out-main \
  -work-dir /workspace/nfc-verify/work-main

# PR branch
cd /workspace/nfc-pr5
nextflow run . -profile test,docker \
  --outdir /workspace/nfc-verify/out-pr \
  -work-dir /workspace/nfc-verify/work-pr
```

Both runs finished with exit 0 (44 processes each).

## Diff summary

```text
=== Scientific tables / FASTA / BAM body ===
OK:   codonyat_summary.tsv
OK:   consensus/consensus_all.fa
OK:   consensus/consensus_stats.tsv
OK:   consensus/{HVG286PL,sample1,sample2}.consensus.fa
OK:   consensus/{HVG286PL,sample1,sample2}.consensus_{indels,stats}.tsv
OK:   contamination/contamination_summary.tsv
OK:   contamination/HVG286PL.contamination.tsv
OK:   samples/{HVG286PL,sample1,sample2}/*.{tsv,xml}
OK:   strand/HVG286PL.strand_metrics_unmerged.tsv
OK:   subtype/subtype_summary.tsv
OK:   subtype/HVG286PL.subtype.tsv
OK:   variants/aa_variants_summary.tsv
OK:   variants/{HVG286PL,sample1,sample2}.aa_variants.tsv
OK:   pipeline_info/methods.md
OK:   pipeline_info/software_versions.yml
OK:   fastp/HVG286PL.fastp.json
OK:   merge/HVG286PL_ihist.txt

BAM alignment/HVG286PL.bam: file bytes differ; samtools view body MD5 identical
  (fe943e84e5f35c9ece57089cb78b644d). Only @PG header differs:
  --threads 2 (main resourceLimits) vs --threads 4 (PR conf/test.config).
  flagstat identical (2183 reads, 98.35% mapped).

=== Expected non-scientific diffs (timestamps / paths / logs) ===
fastqc/*.zip, fastp/*.html, *.bbmerge.log, multiqc_report.html,
multiqc_report_data/{multiqc_data.json,multiqc_sources.txt,multiqc.log,multiqc.parquet},
pipeline_info/{execution_*.html,execution_trace.txt,provenance.json}
```

`provenance.json` also records absolute input paths and the new params
(`help`, `validate_params`, `config_profile_*`, `pipeline_info_outdir`) that
exist only on the PR branch; no scientific field differs.

## Conclusion

Every TSV / FASTA / BAM-derived table matches. The only BAM byte difference is
the Bowtie2/samtools `@PG` thread count from the CI-friendly resourceLimits
change in `conf/test.config` (2 → 4 CPUs). No analysis parameters or tool
versions changed (codonyat 1.1.0 from PyPI on both sides).
