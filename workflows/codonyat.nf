/*
 * =========================================================
 *  workflows/codonyat.nf
 *
 *  Main pipeline workflow.
 * =========================================================
 */

include { CODONYAT_RUN }     from '../modules/codonyat/run/main.nf'
include { CODONYAT_SUMMARY } from '../modules/codonyat/summary/main.nf'

workflow CODONYAT {
    take:
    samples_ch      // [val(sample_id), path(sam)]  from VALIDATE_INPUT
    reference_ch    // path
    amplicons_ch    // path

    main:

    // ── 1. Scatter: run codonyat per sample ────────────────
    CODONYAT_RUN(
        samples_ch,
        reference_ch,
        amplicons_ch
    )
    // → results: [sample_id, tsv, xml]

    // ── 2. Generate combined summary TSV ──────────────────
    // Flatten per-sample channel into a flat list of TSV files for the summary process
    CODONYAT_RUN.out.results
        .map { sample_id, tsv, xml -> tsv }
        .collect()
        .set { all_tsvs }

    CODONYAT_SUMMARY(all_tsvs)

    // ── 3. Publish per-sample XML files
    // Already published via publishDir in CODONYAT_RUN
    // CODONYAT_RUN.out.results.map { ... } — individual XMLs per sample

    emit:
    per_sample = CODONYAT_RUN.out.results   // [id, tsv, xml] per sample
    summary    = CODONYAT_SUMMARY.out.combined_tsv  // path
}
