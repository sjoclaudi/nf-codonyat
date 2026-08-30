/*
 * =========================================================
 *  modules/codonyat/summary/main.nf
 *
 *  Process: CODONYAT_SUMMARY
 *  Merges per-sample TSV files into one combined table,
 *  adding a SAMPLE column.
 *
 *  Input  : one or more TSV files from per-sample runs
 *  Output : codonyat_summary.tsv
 * =========================================================
 */

process CODONYAT_SUMMARY {
    tag "CODONYAT_SUMMARY"

    label 'process_low'

    publishDir "${params.outdir}", mode: params.publish_dir_mode, pattern: '*.tsv'

    input:
    path 'inputs/*'

    output:
    path 'codonyat_summary.tsv', emit: combined_tsv
    path 'inputs/*.xml',         emit: xml_files, optional: true

    script:
    """
    codonyat_summary.py inputs/*.tsv > codonyat_summary.tsv
    """
}
