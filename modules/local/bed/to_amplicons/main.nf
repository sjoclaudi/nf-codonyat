/*
 * BED_TO_AMPLICONS: Convert 6-column primer BED to amplicons TSV
 */
process BED_TO_AMPLICONS {
    tag "${bed.baseName}"
    label 'process_single'

    conda "${moduleDir}/../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.5.0'

    input:
    path reference
    path bed

    output:
    path "amplicons.tsv", emit: amplicons
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    """
    bed_to_amplicons.py \\
        --reference "${reference}" \\
        --primer-bed "${bed}" \\
        --out amplicons.tsv
    """
}
