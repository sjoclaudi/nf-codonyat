/*
 * IVAR_CONSENSUS_RECORDS: iVar consensus per FASTA record.
 * One-record references use the same samtools mpileup | ivar command as
 * nf-core/ivar/consensus so HIV-1 output stays unchanged.
 */
process IVAR_CONSENSUS_RECORDS {
    tag "${meta.id}"
    label 'process_medium'

    conda "${moduleDir}/../../../nf-core/ivar/consensus/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/ivar:1.4.4--h077b44d_0' :
        'quay.io/biocontainers/ivar:1.4.4--h077b44d_0' }"

    input:
    tuple val(meta), path(bam)
    path fasta

    output:
    tuple val(meta), path("${prefix}.fa")     , emit: fasta
    tuple val(meta), path("${prefix}.mpileup"), emit: mpileup
    tuple val("${task.process}"), val('ivar'), eval("ivar version | sed -n 's|iVar version \\(.*\\)|\\1|p'"), topic: versions, emit: versions_ivar

    script:
    def args = task.ext.args ?: ''
    def args2 = task.ext.args2 ?: '-aa -A -B -d 0 -Q 0'
    prefix = task.ext.prefix ?: "${meta.id}.ivar"
    """
    set -euo pipefail
    n=\$(grep -c '^>' "${fasta}" || true)
    if [ "\$n" -le 1 ]; then
        samtools mpileup --reference "${fasta}" ${args2} "${bam}" \\
            | tee "${prefix}.mpileup" \\
            | ivar consensus ${args} -p "${prefix}"
    else
        samtools index "${bam}"
        : > "${prefix}.fa"
        : > "${prefix}.mpileup"
        grep '^>' "${fasta}" | sed 's/^>//' | awk '{print \$1}' | while read -r rec; do
            safe=\$(echo "\$rec" | tr '/| ' '___')
            samtools view -b "${bam}" "\$rec" > "\${safe}.bam"
            samtools mpileup --reference "${fasta}" ${args2} "\${safe}.bam" \\
                | tee "\${safe}.mpileup" \\
                | ivar consensus ${args} -p "\${safe}"
            # iVar writes a single header; rename to the contig id
            if [ -f "\${safe}.fa" ]; then
                awk -v rec="\$rec" 'BEGIN{n=0} /^>/{print ">" rec; n=1; next} {print}' "\${safe}.fa" >> "${prefix}.fa"
            fi
            cat "\${safe}.mpileup" >> "${prefix}.mpileup"
        done
    fi
    """
}
