#!/usr/bin/env nextflow
/*
 * =========================================================
 *  nf-codonyat  –  main.nf
 *  Codon-aware amino acid variant typing pipeline
 * =========================================================
 *
 *  Usage:
 *    nextflow run sjoclaudi/nf-codonyat -profile docker \
 *        --input samples.csv \
 *        --kraken2_db /path/to/k2_standard_08 \
 *        --outdir results
 *
 *    nextflow run sjoclaudi/nf-codonyat -profile test,docker
 *
 *    nextflow run sjoclaudi/nf-codonyat -profile awsbatch \
 *        -work-dir s3://codonyat/nf-work \
 *        --kraken2_db s3://codonyat/refdb/... --outdir s3://codonyat/results
 *
 *  Research use only.
 */

include { VALIDATE_INPUT      } from './subworkflows/validate_input'
include { CODONYAT            } from './workflows/codonyat'
include { PREPARE_REFERENCE; CHECK_VALIDATION } from './modules/local/prepare/inputs/main'
include { validateParameters  } from 'plugin/nf-schema'

def placeholder(String name) {
    file("${projectDir}/assets/placeholders/${name}", checkIfExists: true)
}

def parsePresetYml(java.nio.file.Path yml) {
    def cfg = [:]
    def listKey = null
    yml.eachLine { raw ->
        def line = raw.replaceFirst(/#.*$/, '').trim()
        if (!line) {
            return
        }
        if (line.startsWith('- ')) {
            if (listKey) {
                if (!(cfg[listKey] instanceof List)) {
                    cfg[listKey] = []
                }
                cfg[listKey] << line.substring(2).trim().replaceAll(/^['"]|['"]$/, '')
            }
            return
        }
        def idx = line.indexOf(':')
        if (idx < 0) {
            return
        }
        def key = line.substring(0, idx).trim()
        def value = line.substring(idx + 1).trim()
        listKey = key
        if (!value) {
            cfg[key] = []
            return
        }
        if (value.isInteger()) {
            cfg[key] = value as int
        } else if (value in ['true', 'false']) {
            cfg[key] = value == 'true'
        } else {
            cfg[key] = value.replaceAll(/^['"]|['"]$/, '')
        }
    }
    return cfg
}

def loadPreset(String name) {
    if (name == 'custom') {
        return [
            reference            : null,
            amplicons            : null,
            primer_bed           : null,
            subtype_panel        : null,
            target_taxid         : null,
            target_label         : 'TARGET',
            requires_primer_bed  : true,
            primer_unverified    : false,
        ]
    }
    def dir = file("${projectDir}/assets/presets/${name}", checkIfExists: true)
    def yml = dir.resolve('preset.yml')
    if (!yml.exists()) {
        error "Preset '${name}' is missing assets/presets/${name}/preset.yml"
    }
    def cfg = parsePresetYml(yml)
    def ref = dir.resolve('reference.fasta')
    def amp = dir.resolve('amplicons.tsv')
    def bed = dir.resolve('primers.bed')
    def panel = dir.resolve('subtype_panel')
    return [
        reference           : ref.exists() ? ref.toString() : null,
        amplicons           : amp.exists() ? amp.toString() : null,
        primer_bed          : bed.exists() ? bed.toString() : null,
        subtype_panel       : (panel.exists() && panel.isDirectory()) ? panel.toString() : null,
        target_taxid        : cfg.target_taxid,
        target_label        : cfg.target_label ?: 'TARGET',
        requires_primer_bed : cfg.requires_primer_bed ? true : false,
        primer_unverified   : cfg.primer_unverified ? true : false,
    ]
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
    primers     : ${params.primer_bed ?: params.amplicons ?: 'from preset'}
    protein     : ${params.protein}
    kraken2_db  : ${params.skip_contamination ? 'skipped' : params.kraken2_db ?: '(none)'}
    subtype     : ${params.skip_subtype ? 'skipped' : params.subtype_panel ?: 'from preset'}
    merge_pairs : ${params.merge_pairs}
    consensus   : ${params.skip_consensus ? 'skipped' : "t=${params.consensus_threshold}, min depth ${params.consensus_min_depth}x"}
    outdir      : ${params.outdir}
    -------------------------------------------------------
    """.stripIndent()
}

workflow {
    main:
    def help_requested = params.help || params.helpFull
    if (!help_requested) {

    def preset_cfg = loadPreset(params.preset as String)
    def samplesheet = params.input ?: params.samplesheet
    def reference = params.reference ?: preset_cfg.reference
    def amplicons = params.amplicons
    def primer_bed = params.primer_bed
    def annotation = params.annotation
    def target_taxid = params.target_taxid ?: preset_cfg.target_taxid
    def target_label = params.target_label ?: preset_cfg.target_label
    def subtype_panel = params.subtype_panel ?: preset_cfg.subtype_panel

    if (!amplicons && !primer_bed) {
        amplicons = preset_cfg.amplicons
        primer_bed = preset_cfg.primer_bed
    }

    if (!params.validate_only && !samplesheet) {
        error "Missing required parameter(s): --samplesheet"
    }
    if (params.preset == 'custom' && !reference) {
        error "Custom preset requires --reference"
    }
    if (!reference) {
        error "No reference provided and preset '${params.preset}' has no reference"
    }
    if (amplicons && primer_bed) {
        error "Cannot specify both --amplicons and --primer_bed (mutually exclusive)"
    }
    if (!amplicons && !primer_bed) {
        if (params.preset != 'custom' && (preset_cfg.requires_primer_bed || preset_cfg.primer_unverified)) {
            error "Preset '${params.preset}' has no bundled primer scheme (unverified). Provide --primer_bed or --amplicons."
        } else if (params.preset == 'custom' || preset_cfg.requires_primer_bed) {
            error "Must provide either --amplicons (TSV) or --primer_bed (6-column BED)"
        }
        // requires_primer_bed false: skip primer trimming; write whole-record
        // placeholder amplicon rows so codonyat 1.3.1 accepts the TSV
    }

    if (params.validate_params) {
        validateParameters()
    }

    // Deprecated alias: honour --contamination_warn_hiv_pct when the new param is still at default
    def warn_target = params.contamination_warn_target_pct
    if (params.contamination_warn_hiv_pct != params.contamination_warn_target_pct
            && params.contamination_warn_target_pct == 50) {
        warn_target = params.contamination_warn_hiv_pct
    }

    def auto_skip_contamination = (params.preset == 'custom') && (!params.kraken2_db || !target_taxid)
    // hiv1 still requires a DB for FASTQ unless --skip_contamination (checked in VALIDATE_INPUT)
    def run_contamination = !params.skip_contamination && params.kraken2_db && target_taxid && !auto_skip_contamination
    def kraken2_skip_reason = null
    if (params.skip_contamination) {
        kraken2_skip_reason = 'skip_contamination'
    } else if (auto_skip_contamination && !params.kraken2_db) {
        kraken2_skip_reason = 'custom_mode_no_kraken2_db'
    } else if (auto_skip_contamination && !target_taxid) {
        kraken2_skip_reason = 'custom_mode_no_target_taxid'
    }

    def subtype_skipped = params.skip_subtype || !subtype_panel

    if (params.pipeline_info_outdir && file(params.pipeline_info_outdir.toString()) != file(params.outdir.toString())) {
        log.warn "params.outdir was set in a config file passed with -c ('${params.outdir}'). " +
                 "Results go there, but the execution reports (timeline, report, trace, DAG) are written to " +
                 "'${file(params.pipeline_info_outdir.toString())}/pipeline_info' because Nextflow places them before -c files are read. " +
                 "Use --outdir or -params-file to keep results and reports together."
    }

    printHeader()

    def meta = [
        preset               : params.preset,
        target_taxid         : target_taxid,
        target_label         : target_label,
        kraken2_skipped      : !run_contamination,
        kraken2_skip_reason  : run_contamination ? '' : (kraken2_skip_reason ?: 'no_kraken2_db'),
        subtype_skipped      : subtype_skipped,
        warn_target_pct      : warn_target,
        protein              : params.protein,
    ]

    PREPARE_REFERENCE(
        file(reference, checkIfExists: true),
        primer_bed ? file(primer_bed, checkIfExists: true) : placeholder('NO_PRIMER_BED'),
        amplicons  ? file(amplicons,  checkIfExists: true) : placeholder('NO_AMPLICONS'),
        annotation ? file(annotation, checkIfExists: true) : placeholder('NO_ANNOTATION'),
        samplesheet ? file(samplesheet, checkIfExists: true) : placeholder('NO_SAMPLESHEET'),
        meta
    )

    CHECK_VALIDATION(PREPARE_REFERENCE.out.validation)

    if (params.validate_only) {
        log.info "validate_only: wrote ${params.outdir}/reference/validation.json (no Kraken2 or alignment)"
    } else {
    VALIDATE_INPUT(
        samplesheet,
        reference,
        auto_skip_contamination
    )

    def fasta_ok = CHECK_VALIDATION.out.json
        .combine(PREPARE_REFERENCE.out.fasta)
        .map { _json, fasta -> fasta }
        .first()
    def amplicons_ok = CHECK_VALIDATION.out.json
        .combine(PREPARE_REFERENCE.out.amplicons)
        .map { _json, amp -> amp }
        .first()

    CODONYAT(
        VALIDATE_INPUT.out.fastq,
        VALIDATE_INPUT.out.sam,
        fasta_ok,
        amplicons_ok,
        target_taxid,
        target_label,
        subtype_panel,
        run_contamination,
        warn_target
    )
    }
    }
}
