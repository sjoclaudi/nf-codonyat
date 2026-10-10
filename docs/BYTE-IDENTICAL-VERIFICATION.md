# Byte-identical verification vs v0.3.1 (`9b11f81`)

Research use only. This documents a real run of `-profile test,docker` on
`main@9b11f81` and on this PR branch, into separate outdirs, then a recursive
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
