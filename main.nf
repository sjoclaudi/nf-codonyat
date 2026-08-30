#!/usr/bin/env nextflow
/*
 * =========================================================
 *  nf-codonyat  –  main.nf
 *  Codon-aware amino acid variant typing pipeline
 * =========================================================
 *
 *  Usage:
 *    nextflow run mnoguera/nf-codonyat \
 *        --samplesheet samples.csv \
 *        --reference ref.fasta \
 *        --amplicons amplicons.tsv \
 *        --outdir results
 *
 *    nextflow run . -profile docker \
 *        --samplesheet samples.csv \
 *        --reference ref.fasta \
 *        --amplicons amplicons.tsv
 */

nextflow.enable.dsl = 2

// ─── Print version & header ─────────────────────────────────

def printVersion() {
    log.info"""
    ╔══════════════════════════════════════════════════════╗
    ║  nf-codonyat  v${manifest.version}                               ║
    ║  Codon-aware amino acid variant typing               ║
    ║  https://github.com/mnoguera/nf-codonyat             ║
    ╚══════════════════════════════════════════════════════╝
    """.stripIndent()
}

// ─── Validate required params before any expensive work ─────

if (!params.samplesheet) {
    log.error 'ERROR: --samplesheet is required. See --help.'
    exit 1
}
if (!params.reference) {
    log.error 'ERROR: --reference is required.'
    exit 1
}
if (!params.amplicons) {
    log.error 'ERROR: --amplicons is required.'
    exit 1
}

// ─── Load subworkflows & workflows ─────────────────────────

include { VALIDATE_INPUT } from './subworkflows/validate_input'
include { CODONYAT }       from './workflows/codonyat'

// ─── Main workflow ─────────────────────────────────────────

workflow {
    printVersion()

    // Validate samplesheet, reference, and amplicons
    // Pass plain values (not channels) — subworkflow wraps them internally
    VALIDATE_INPUT(
        params.samplesheet,
        params.reference,
        params.amplicons
    )

    // Run the codonyat pipeline
    // VALIDATE_INPUT.out.samples  → [val(sample_id), path(sam_file)]
    // VALIDATE_INPUT.out.reference → path
    // VALIDATE_INPUT.out.amplicons → path
    CODONYAT(
        VALIDATE_INPUT.out.samples,
        VALIDATE_INPUT.out.reference,
        VALIDATE_INPUT.out.amplicons
    )
}
