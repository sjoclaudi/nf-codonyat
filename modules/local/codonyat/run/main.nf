/*
 * =========================================================
 *  modules/local/codonyat/run/main.nf
 *
 *  Process: CODONYAT_RUN
 *
 *  Wraps:  codonyat-runner <sam> <ref.fasta> <amplicons.tsv>
 *          --protein --ratio-upper --ratio-lower --entropy-threshold
 *          --csv-path <sample>.tsv --xml-path <sample>.xml
 *
 *  Input  : tuple val(meta), path(sam); path(reference); path(amplicons)
 *  Output : tuple val(meta), path(<sample>.tsv), path(<sample>.xml)
 *  The SAM is linked as <sample>.sam so the FILE column shows the sample id.
 * =========================================================
 */

process CODONYAT_RUN {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.1.0'

    input:
    tuple val(meta), path(sam)
    path reference
    path amplicons

    output:
    tuple val(meta), path("${meta.id}.tsv"), path("${meta.id}.xml"), emit: results

    script:
    """
    [ "${sam}" = "${meta.id}.sam" ] || ln -s "${sam}" "${meta.id}.sam"

    codonyat-runner \\
        "${meta.id}.sam" \\
        "${reference}" \\
        "${amplicons}" \\
        --protein "${params.protein}" \\
        --ratio-upper ${params.ratio_upper} \\
        --ratio-lower ${params.ratio_lower} \\
        --entropy-threshold ${params.entropy_threshold} \\
        --csv-path "${meta.id}.tsv" \\
        --xml-path "${meta.id}.xml"
    """
}
