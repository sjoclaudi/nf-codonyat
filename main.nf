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

    // The execution reports are placed using params.outdir as it was when
    // nextflow.config was read (see the note there). A -c config that changes
    // params.outdir afterwards cannot move them, so tell the user where they are.
    if (params.pipeline_info_outdir && file(params.pipeline_info_outdir.toString()) != file(params.outdir.toString())) {
        log.warn "params.outdir was set in a config file passed with -c ('${params.outdir}'). " +
                 "Results go there, but the execution reports (timeline, report, trace, DAG) are written to " +
                 "'${file(params.pipeline_info_outdir.toString())}/pipeline_info' because Nextflow places them before -c files are read. " +
                 "Use --outdir or -params-file to keep results and reports together."
    }

    printHeader()

    VALIDATE_INPUT(
        params.samplesheet,
        params.reference,
        params.amplicons
    )

    CODONYAT(
        VALIDATE_INPUT.out.fastq,
        VALIDATE_INPUT.out.sam,
        VALIDATE_INPUT.out.reference,
        VALIDATE_INPUT.out.amplicons
    )
}
