#!/usr/bin/env nextflow
/*
 * =========================================================
 *  nf-codonyat  –  main.nf
 *  Codon-aware amino acid variant typing pipeline
 * =========================================================
 *
 *  Usage:
 *    nextflow run sjoclaudi/nf-codonyat -profile docker \
 *        --samplesheet samples.csv \
 *        --reference ref.fasta \
 *        --amplicons amplicons.tsv \
 *        --outdir results
 *
 *    nextflow run sjoclaudi/nf-codonyat -profile test,docker
 */

include { VALIDATE_INPUT } from './subworkflows/validate_input'
include { CODONYAT       } from './workflows/codonyat'

def printHeader() {
    log.info """
    nf-codonyat v${workflow.manifest.version}
    Codon-aware amino acid variant typing
    ${workflow.manifest.homePage}
    -------------------------------------------------------
    samplesheet : ${params.samplesheet}
    reference   : ${params.reference}
    amplicons   : ${params.amplicons}
    protein     : ${params.protein}
    outdir      : ${params.outdir}
    -------------------------------------------------------
    """.stripIndent()
}

workflow {
    main:
    // Fail fast on missing required parameters, before any work is scheduled
    def missing = ['samplesheet', 'reference', 'amplicons'].findAll { name -> !params[name] }
    if (missing) {
        error "Missing required parameter(s): ${missing.collect { name -> '--' + name }.join(', ')}"
    }

    printHeader()

    VALIDATE_INPUT(
        params.samplesheet,
        params.reference,
        params.amplicons
    )

    CODONYAT(
        VALIDATE_INPUT.out.samples,
        VALIDATE_INPUT.out.reference,
        VALIDATE_INPUT.out.amplicons
    )
}
