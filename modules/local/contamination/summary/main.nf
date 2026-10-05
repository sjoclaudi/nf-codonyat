/*
 *  CONTAMINATION_SUMMARY: Kraken2 report -> <sample>.contamination.tsv (report-only QC).
 */
process CONTAMINATION_SUMMARY {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    tuple val(meta), path(report)

    output:
    tuple val(meta), path("${meta.id}.contamination.tsv"), emit: tsv
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    """
    contamination_summary.py sample \\
        --sample "${meta.id}" \\
        --report "${report}" \\
        --warn-hiv-pct ${params.contamination_warn_hiv_pct} \\
        --warn-human-pct ${params.contamination_warn_human_pct} \\
        > "${meta.id}.contamination.tsv"
    """
}
