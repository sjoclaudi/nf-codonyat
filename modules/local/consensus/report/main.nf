/*
 *  CONSENSUS_REPORT: iVar consensus + mpileup -> renamed consensus FASTA,
 *  indel table (frameshift flag) and consensus statistics.
 */
process CONSENSUS_REPORT {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    tuple val(meta), path(fasta), path(mpileup)
    val reference_id

    output:
    tuple val(meta), path("${meta.id}.consensus.fa")        , emit: fasta
    tuple val(meta), path("${meta.id}.consensus_indels.tsv"), emit: indels
    tuple val(meta), path("${meta.id}.consensus_stats.tsv") , emit: stats
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    """
    consensus_report.py \\
        --sample "${meta.id}" \\
        --fasta "${fasta}" \\
        --mpileup "${mpileup}" \\
        --reference-id "${reference_id}" \\
        --threshold ${params.consensus_threshold} \\
        --insertion-threshold ${params.consensus_insertion_threshold} \\
        --min-depth ${params.consensus_min_depth}
    """
}
