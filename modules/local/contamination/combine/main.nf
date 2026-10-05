/*
 *  CONTAMINATION_COMBINE: per-sample contamination tables -> contamination_summary.tsv + MultiQC table.
 */
process CONTAMINATION_COMBINE {
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    path tables, stageAs: 'inputs/*'

    output:
    path 'contamination_summary.tsv', emit: tsv
    path 'contamination_mqc.tsv'    , emit: mqc

    script:
    """
    contamination_summary.py combine inputs/* --out contamination_summary.tsv --mqc contamination_mqc.tsv
    """
}
