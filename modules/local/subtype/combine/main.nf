/*
 *  SUBTYPE_COMBINE: per-sample subtype tables -> subtype_summary.tsv + MultiQC table.
 */
process SUBTYPE_COMBINE {
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    path tables, stageAs: 'inputs/*'

    output:
    path 'subtype_summary.tsv', emit: tsv
    path 'subtype_mqc.tsv'    , emit: mqc

    script:
    """
    estimate_subtype.py combine inputs/* --out subtype_summary.tsv --mqc subtype_mqc.tsv
    """
}
