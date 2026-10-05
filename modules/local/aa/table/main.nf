/*
 *  CODON_TO_AA: codonyat codon table -> <sample>.aa_variants.tsv
 *  (amino-acid frequencies only; no drug, resistance or clinical annotation).
 *  The optional strand table adds *_UNMERGED strand columns (D9).
 */
process CODON_TO_AA {
    tag "${meta.id}"
    label 'process_single'

    conda "${moduleDir}/../../codonyat/run/environment.yml"
    container 'ghcr.io/sjoclaudi/nf-codonyat:0.3.0'

    input:
    tuple val(meta), path(codon_tsv), path(strand_tsv)
    path reference

    output:
    tuple val(meta), path("${meta.id}.aa_variants.tsv"), emit: tsv
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    script:
    def strand = strand_tsv ? "--strand ${strand_tsv}" : ''
    """
    codon_to_aa.py --sample "${meta.id}" --codons "${codon_tsv}" --reference "${reference}" ${strand} \\
        > "${meta.id}.aa_variants.tsv"
    """
}
