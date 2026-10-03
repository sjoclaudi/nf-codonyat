/*
 * =========================================================
 *  modules/codonyat/run/main.nf
 *
 *  Process: CODONYAT_RUN
 *
 *  Wraps:  codonyat-runner <sam> <ref.fasta> <amplicons.tsv>
 *          --protein --ratio-upper --ratio-lower --entropy-threshold
 *          --csv-path <sample>.tsv --xml-path <sample>.xml
 *
 *  Input  : tuple val(sample_id), path(sam); path(reference); path(amplicons)
 *  Output : tuple val(sample_id), path(<sample>.tsv), path(<sample>.xml)
 * =========================================================
 */

process CODONYAT_RUN {
    tag "${sample_id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.1.0'

    input:
    tuple val(sample_id), path(sam)
    path reference
    path amplicons

    output:
    tuple val(sample_id), path("${sample_id}.tsv"), path("${sample_id}.xml"), emit: results

    script:
    """
    codonyat-runner \\
        "${sam}" \\
        "${reference}" \\
        "${amplicons}" \\
        --protein "${params.protein}" \\
        --ratio-upper ${params.ratio_upper} \\
        --ratio-lower ${params.ratio_lower} \\
        --entropy-threshold ${params.entropy_threshold} \\
        --csv-path "${sample_id}.tsv" \\
        --xml-path "${sample_id}.xml"
    """
}
