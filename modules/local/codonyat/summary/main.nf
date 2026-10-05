/*
 * =========================================================
 *  modules/local/codonyat/summary/main.nf
 *
 *  Process: CODONYAT_SUMMARY
 *  Merges per-sample TSV files into one table, prepending a
 *  SAMPLE column (taken from the file name, i.e. the sample id).
 *
 *  Input  : list of per-sample TSV files
 *  Output : codonyat_summary.tsv
 * =========================================================
 */

process CODONYAT_SUMMARY {
    label 'process_low'

    // Only needs Python 3; reuse the pipeline environment/image
    conda "${moduleDir}/../run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    path tsvs, stageAs: 'inputs/*'

    output:
    path 'codonyat_summary.tsv', emit: combined_tsv

    script:
    """
    codonyat_summary.py inputs/*.tsv > codonyat_summary.tsv
    """
}
