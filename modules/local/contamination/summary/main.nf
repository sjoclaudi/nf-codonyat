/*
 *  CONTAMINATION_SUMMARY: Kraken2 report -> <sample>.contamination.tsv (report-only QC).
 */
process CONTAMINATION_SUMMARY {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.6.0'

    input:
    tuple val(meta), path(report)
    val target_taxid
    val target_label
    val warn_target_pct

    output:
    tuple val(meta), path("${meta.id}.contamination.tsv"), emit: tsv
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    def taxid_arg = target_taxid ? "--target-taxid ${target_taxid}" : ""
    def label_arg = target_label ? "--target-label ${target_label}" : ""
    """
    contamination_summary.py sample \\
        --sample "${meta.id}" \\
        --report "${report}" \\
        ${taxid_arg} \\
        ${label_arg} \\
        --warn-target-pct ${warn_target_pct} \\
        --warn-human-pct ${params.contamination_warn_human_pct} \\
        > "${meta.id}.contamination.tsv"
    """

    stub:
    """
    touch "${meta.id}.contamination.tsv"
    """
}
