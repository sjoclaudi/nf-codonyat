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
 *        --kraken2_db /path/to/k2_standard_08 \
 *        --outdir results
 *
 *    nextflow run sjoclaudi/nf-codonyat -profile test,docker
 */

include { VALIDATE_INPUT } from './subworkflows/validate_input'
include { CODONYAT       } from './workflows/codonyat'
include { validateParameters } from 'plugin/nf-schema'

def printHeader() {
    log.info """
    nf-codonyat v${workflow.manifest.version}
    Codon-aware amino acid variant typing (research use only)
    ${workflow.manifest.homePage}
    -------------------------------------------------------
    samplesheet : ${params.samplesheet}
    reference   : ${params.reference}
    amplicons   : ${params.amplicons}
    protein     : ${params.protein}
    kraken2_db  : ${params.skip_contamination ? 'skipped' : params.kraken2_db}
    subtype     : ${params.skip_subtype ? 'skipped' : params.subtype_panel}
    merge_pairs : ${params.merge_pairs}
    consensus   : ${params.skip_consensus ? 'skipped' : "t=${params.consensus_threshold}, min depth ${params.consensus_min_depth}x"}
    outdir      : ${params.outdir}
    -------------------------------------------------------
    """.stripIndent()
}

workflow {
    main:
    // nf-schema: HelpObserver prints --help/--helpFull; do not schedule work when help was requested
    def help_requested = params.help || params.helpFull
    if (help_requested) {
        return
    }

    // Fail fast on missing required parameters (clear --prefixed message for users and nf-test)
    def missing = ['samplesheet', 'reference', 'amplicons'].findAll { name -> !params[name] }
    if (missing) {
        error "Missing required parameter(s): ${missing.collect { name -> '--' + name }.join(', ')}"
    }

    if (params.validate_params) {
        validateParameters()
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
