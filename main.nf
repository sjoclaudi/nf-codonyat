#!/usr/bin/env nextflow
/*
 * =========================================================
 *  nf-codonyat  –  main.nf
 *  Codon-aware amino acid variant typing pipeline
 * =========================================================
 *
 *  Usage:
 *    # HIV-1 (default preset)
 *    nextflow run sjoclaudi/nf-codonyat -profile docker \
 *        --input samples.csv \
 *        --kraken2_db /path/to/k2_standard_08 \
 *        --outdir results
 *
 *    # Custom virus with primer BED
 *    nextflow run sjoclaudi/nf-codonyat -profile docker \
 *        --preset custom \
 *        --input samples.csv \
 *        --reference ref.fasta \
 *        --primer-bed primers.bed \
 *        --annotation genes.gff3 \
 *        --target-taxid 2697049 \
 *        --target-label "SARS-CoV-2" \
 *        --outdir results
 *
 *    nextflow run sjoclaudi/nf-codonyat -profile test,docker
 */

include { VALIDATE_INPUT } from './subworkflows/validate_input'
include { CODONYAT       } from './workflows/codonyat'
include { validateParameters } from 'plugin/nf-schema'

def loadPreset(String preset) {
    if (preset == 'custom') {
        return [
            reference: null,
            amplicons: null,
            primer_bed: null,
            subtype_panel: null,
            target_taxid: null,
            target_label: 'TARGET'
        ]
    }
    
    // Load preset configuration
    def presetJson = "${projectDir}/bin/load_preset.py --preset ${preset} --project-dir ${projectDir}".execute().text
    return new groovy.json.JsonSlurper().parseText(presetJson)
}

def printHeader() {
    log.info """
    nf-codonyat v${workflow.manifest.version}
    Codon-aware amino acid variant typing (research use only)
    ${workflow.manifest.homePage}
    -------------------------------------------------------
    preset      : ${params.preset}
    samplesheet : ${params.input ?: params.samplesheet}
    reference   : ${params.reference ?: 'from preset'}
    amplicons   : ${params.amplicons ?: 'from preset/primers'}
    protein     : ${params.protein}
    kraken2_db  : ${params.skip_contamination ? 'skipped' : params.kraken2_db ?: 'auto-skip (custom without DB)'}
    subtype     : ${params.skip_subtype ? 'skipped' : params.subtype_panel ?: 'from preset'}
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

    // Load preset configuration
    def preset = loadPreset(params.preset)
    
    // Resolve parameters (user-provided overrides preset)
    def samplesheet = params.input ?: params.samplesheet
    def reference = params.reference ?: preset.reference
    def amplicons = params.amplicons
    def primer_bed = params.primer_bed
    def annotation = params.annotation
    def target_taxid = params.target_taxid ?: preset.target_taxid
    def target_label = params.target_label ?: preset.target_label
    def subtype_panel = params.subtype_panel ?: preset.subtype_panel
    
    // If no user amplicons/primer_bed, use preset values
    if (!amplicons && !primer_bed) {
        amplicons = preset.amplicons
        primer_bed = preset.primer_bed
    }
    
    // Validation: required parameters
    if (!samplesheet) {
        error "Missing required parameter: --input (or --samplesheet)"
    }
    
    if (params.preset == 'custom') {
        if (!reference) {
            error "Custom preset requires --reference"
        }
        if (!amplicons && !primer_bed) {
            error "Custom preset requires either --primer-bed or --amplicons"
        }
    }
    
    if (!reference) {
        error "No reference provided and preset '${params.preset}' has no reference"
    }
    
    // Check amplicons XOR primer_bed
    if (amplicons && primer_bed) {
        error "Cannot specify both --amplicons and --primer-bed (mutually exclusive)"
    }
    
    if (!amplicons && !primer_bed) {
        error "Must provide either --amplicons (TSV) or --primer-bed (6-column BED)"
    }

    if (params.validate_params) {
        validateParameters()
    }

    // Validation-only mode: validate inputs and exit
    // Note: Full validation module implementation would be needed for production
    if (params.validate_only) {
        log.info "Validation-only mode enabled. Full implementation pending."
        log.info "Would validate: reference=${reference}, primer_bed=${primer_bed}, annotation=${annotation}"
        error "--validate_only not fully implemented yet. Please remove this flag to run the full pipeline."
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

    // TODO: If primer_bed provided, need to convert to amplicons TSV
    // For now, preset must provide amplicons directly or user must provide --amplicons
    if (primer_bed && !amplicons) {
        error "primer_bed support not yet fully implemented. Please use --amplicons TSV format or a preset with amplicons."
    }
    
    VALIDATE_INPUT(
        samplesheet,
        reference,
        amplicons
    )

    CODONYAT(
        VALIDATE_INPUT.out.fastq,
        VALIDATE_INPUT.out.sam,
        VALIDATE_INPUT.out.reference,
        VALIDATE_INPUT.out.amplicons,
        target_taxid,
        target_label,
        subtype_panel
    )
}
