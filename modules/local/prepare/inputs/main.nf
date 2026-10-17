/*
 * PREPARE_REFERENCE: validate inputs and write reference/ + run_mode.json.
 * Always succeeds so validation.json is published; the workflow fails when valid=false.
 */
process PREPARE_REFERENCE {
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.7.0-dev'

    input:
    path reference
    path primer_bed
    path amplicons
    path annotation
    path samplesheet
    val  meta

    output:
    path 'validation.json'      , emit: validation
    path 'reference_used.fasta' , emit: fasta
    path 'annotation_used.tsv'  , emit: annotation
    path 'amplicons_used.tsv'   , emit: amplicons
    path 'run_mode.json'        , emit: run_mode
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    def bed_arg   = primer_bed.name  in ['NO_FILE', 'NO_PRIMER_BED'] ? '' : "--primer-bed '${primer_bed}'"
    def amp_arg   = amplicons.name   in ['NO_FILE', 'NO_AMPLICONS']  ? '' : "--amplicons '${amplicons}'"
    def ann_arg   = annotation.name  in ['NO_FILE', 'NO_ANNOTATION'] ? '' : "--annotation '${annotation}'"
    def ss_arg    = samplesheet.name in ['NO_FILE', 'NO_SAMPLESHEET'] ? '' : "--samplesheet '${samplesheet}'"
    def taxid     = meta.target_taxid != null ? "${meta.target_taxid}" : ''
    def label     = meta.target_label ?: ''
    def skip_k    = meta.kraken2_skipped ? 'true' : 'false'
    def reason    = meta.kraken2_skip_reason ?: ''
    def skip_s    = meta.subtype_skipped ? 'true' : 'false'
    """
    prepare_inputs.py \\
        --reference '${reference}' \\
        ${bed_arg} \\
        ${amp_arg} \\
        ${ann_arg} \\
        ${ss_arg} \\
        --preset '${meta.preset}' \\
        --pipeline-version '${workflow.manifest.version}' \\
        --target-taxid '${taxid}' \\
        --target-label '${label}' \\
        --kraken2-skipped ${skip_k} \\
        --kraken2-skip-reason '${reason}' \\
        --subtype-skipped ${skip_s} \\
        --protein '${meta.protein ?: 'all'}' \\
        --outdir .
    """

    stub:
    """
    printf '%s\\n' '{' '"valid": true,' '"errors": [],' '"warnings": []' '}' > validation.json
    touch reference_used.fasta annotation_used.tsv amplicons_used.tsv
    echo '{}' > run_mode.json
    """
}

process CHECK_VALIDATION {
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.7.0-dev'

    input:
    path json

    output:
    path json, emit: json

    script:
    """
    check_validation.py "${json}"
    """

    stub:
    """
    echo stub
    """
}
