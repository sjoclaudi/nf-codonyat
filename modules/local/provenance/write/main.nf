/*
 *  PROVENANCE: software_versions.yml, provenance.json (params, versions, SHA-256 of
 *  reference data) and an auto-written methods.md with the research-use-only statement.
 */
process PROVENANCE {
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    path versions
    path params_json
    path reference
    path amplicons
    path panel, stageAs: 'subtype_panel'
    path kraken2_db, stageAs: 'kraken2_db'

    output:
    path 'software_versions.yml', emit: versions_yml
    path 'provenance.json'      , emit: json
    path 'methods.md'           , emit: methods

    script:
    """
    provenance.py \\
        --versions "${versions}" \\
        --params "${params_json}" \\
        --pipeline-version "${workflow.manifest.version}" \\
        --checksum "reference=${reference}" \\
        --checksum "amplicons=${amplicons}" \\
        --checksum "subtype_panel=subtype_panel" \\
        --checksum "kraken2_db=kraken2_db"
    """
}
