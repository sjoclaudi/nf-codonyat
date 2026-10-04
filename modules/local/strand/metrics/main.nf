/*
 *  STRAND_METRICS: codon table of the merged-read alignment + codon table of the
 *  unmerged (pre-merge) pair alignment -> <sample>.strand_metrics_unmerged.tsv
 */
process STRAND_METRICS {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    tuple val(meta), path(merged_tsv), path(unmerged_tsv)

    output:
    tuple val(meta), path("${meta.id}.strand_metrics_unmerged.tsv"), emit: tsv
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    """
    strand_metrics.py --sample "${meta.id}" --merged "${merged_tsv}" --unmerged "${unmerged_tsv}" \\
        > "${meta.id}.strand_metrics_unmerged.tsv"
    """
}
