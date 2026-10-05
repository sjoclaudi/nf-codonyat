/*
 *  SUBTYPE_ESTIMATE: BBSplit refstats -> <sample>.subtype.tsv
 *  (% of reads mapped unambiguously to each panel bin; read-mapping based, research use only).
 */
process SUBTYPE_ESTIMATE {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    tuple val(meta), path(stats)
    val primary_name
    val bins

    output:
    tuple val(meta), path("${meta.id}.subtype.tsv"), emit: tsv
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    """
    estimate_subtype.py sample \\
        --sample "${meta.id}" \\
        --stats "${stats}" \\
        --primary-name "${primary_name}" \\
        --bins "${bins.join(',')}" \\
        --min-reads ${params.subtype_min_reads} \\
        --min-margin ${params.subtype_min_margin} \\
        > "${meta.id}.subtype.tsv"
    """
}
