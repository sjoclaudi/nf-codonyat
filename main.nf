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

// ─── Load subworkflows ──────────────────────────────────────

include { VALIDATE_INPUT } from './subworkflows/validate_input'

// ─── Load workflows ─────────────────────────────────────────

include { CODONYAT } from './workflows/codonyat'

// ─── Main workflow ─────────────────────────────────────────

workflow {
    printVersion()

    // Validate samplesheet, reference, and amplicons
    def (samplesheet_ch, reference_ch, amplicons_ch) = VALIDATE_INPUT()

    // Run the codonyat pipeline
    CODONYAT(
        samplesheet_ch,     // [val(sample_id), path(sam_file)]
        reference_ch,       // path(reference.fasta)
        amplicons_ch        // path(amplicons.tsv)
    )
}
