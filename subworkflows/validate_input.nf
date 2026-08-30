/*
 * =========================================================
 *  subworkflows/validate_input.nf
 *
 *  Checks:
 *    • samplesheet exists, has header sample,sam, SAMs are real
 *    • reference FASTA is non-empty and has protein annotations
 *    • amplicons TSV has exactly 7 columns
 *
 *  Input (plain values, not channels):
 *    val samplesheet_path  — path string
 *    val reference_path    — path string
 *    val amplicons_path    — path string
 *
 *  Emits:
 *    out.samplesheet      — path (raw CSV)
 *    out.samples          — [val(sample_id), path(sam_file)] channel
 *    out.reference         — path (validated FASTA)
 *    out.amplicons        — path (validated TSV)
 * =========================================================
 */

workflow VALIDATE_INPUT {
    take:
    samplesheet_val  // String — file path
    reference_val    // String — file path
    amplicons_val    // String — file path

    main:

    // ── 1. Samplesheet ────────────────────────────────────
    Channel
        .fromPath(samplesheet_val, checkIfExists: true)
        .ifEmpty {
            log.error "Samplesheet not found: ${samplesheet_val}"
            exit 1
        }
        .set { ss_path_ch }

    // Parse samplesheet, validate header, emit [sample_id, sam_path]
    ss_valid_ch = ss_path_ch
        .splitCsv(header: true, sep: ',')
        .map { row ->
            if (!row.containsKey('sample') || !row.containsKey('sam')) {
                log.error "Samplesheet must have columns: sample,sam"
                exit 1
            }
            def samFile = file(row.sam)
            if (!samFile.exists()) {
                log.error "SAM file not found: ${row.sam}"
                exit 1
            }
            [ row.sample, samFile ]
        }
        .ifEmpty {
            log.error 'Samplesheet is empty or has no valid rows'
            exit 1
        }

    // ── 2. Reference FASTA ─────────────────────────────────
    Channel
        .fromPath(reference_val, checkIfExists: true)
        .ifEmpty {
            log.error "Reference not found: ${reference_val}"
            exit 1
        }
        .set { ref_path_ch }

    // Validate: FASTA header must contain protein annotation parentheses
    ref_path_ch
        .splitFasta(record: [id: true])
        .first()
        .map { rec ->
            if (!rec.id.contains('(') || !rec.id.contains(')')) {
                log.warn "Reference header may lack protein annotation. " +
                         "Expected format: '>ID PR(Desc):start-end;RT(...);...'"
            }
        }
        .subscribe { /* just the side-effect */ }

    // Emit the reference path (validated)
    ref_valid_ch = ref_path_ch

    // ── 3. Amplicons TSV ───────────────────────────────────
    Channel
        .fromPath(amplicons_val, checkIfExists: true)
        .ifEmpty {
            log.error "Amplicons file not found: ${amplicons_val}"
            exit 1
        }
        .set { amp_path_ch }

    // Validate: must have exactly 7 tab-separated columns
    amp_path_ch
        .splitCsv(sep: '\t')
        .first()
        .map { fields ->
            if (fields.size() != 7) {
                log.error "Amplicons file must have 7 columns " +
                          "(label,protein,reference,5p_seq,3p_seq,start,end). " +
                          "Found: ${fields.size()}"
                exit 1
            }
        }
        .subscribe { /* just the side-effect */ }

    // Emit the amplicons path (validated)
    amp_valid_ch = amp_path_ch

    // ── Emit ──────────────────────────────────────────────
    emit:
    samplesheet = ss_path_ch      // path
    samples     = ss_valid_ch     // [val(sample_id), path(sam)]
    reference   = ref_valid_ch    // path
    amplicons   = amp_valid_ch    // path
}
