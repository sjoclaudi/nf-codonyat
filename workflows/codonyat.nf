/*
 * =========================================================
 *  workflows/codonyat.nf
 *
 *  1. CODONYAT_RUN      – codonyat-runner per sample (scatter)
 *  2. CODONYAT_SUMMARY  – merge per-sample TSVs (gather)
 * =========================================================
 */

include { CODONYAT_RUN     } from '../modules/codonyat/run/main.nf'
include { CODONYAT_SUMMARY } from '../modules/codonyat/summary/main.nf'

workflow CODONYAT {
    take:
    samples_ch      // queue: [ val(sample_id), path(sam) ]
    reference_ch    // value: path
    amplicons_ch    // value: path

    main:
    CODONYAT_RUN(samples_ch, reference_ch, amplicons_ch)

    all_tsvs = CODONYAT_RUN.out.results
        .map { _sample_id, tsv, _xml -> tsv }
        .collect()

    CODONYAT_SUMMARY(all_tsvs)

    emit:
    per_sample = CODONYAT_RUN.out.results        // [ id, tsv, xml ]
    summary    = CODONYAT_SUMMARY.out.combined_tsv
}
