/*
 * =========================================================
 *  modules/local/codonyat/run/main.nf
 *
 *  Process: CODONYAT_RUN
 *
 *  Wraps:  codonyat-runner <sam> <ref.fasta> <amplicons.tsv>
 *          --protein <name | A,B,C | all> --ratio-upper --ratio-lower
 *          --entropy-threshold --csv-path <prefix>.tsv --xml-path <prefix>.xml
 *
 *  codonyat >= 1.1 streams the alignments (flat memory) and counts every
 *  requested protein in one pass.
 *
 *  Input  : tuple val(meta), path(sam); path(reference); path(amplicons)
 *  Output : tuple val(meta), path(<prefix>.tsv), path(<prefix>.xml)
 *  The SAM is linked as <sample>.sam so the FILE column shows the sample id.
 * =========================================================
 */

process CODONYAT_RUN {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    tuple val(meta), path(sam)
    path reference
    path amplicons

    output:
    tuple val(meta), path("${prefix}.tsv"), path("${prefix}.xml"), emit: results
    tuple val("${task.process}"), val('codonyat'), eval("python3 -c 'import importlib.metadata as m; print(m.version(\"codonyat\"))'"), topic: versions, emit: versions_codonyat

    script:
    prefix = task.ext.prefix ?: "${meta.id}"
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
        --csv-path "${prefix}.tsv" \\
        --xml-path "${prefix}.xml"
    """
}
