/*
 * =========================================================
 *  subworkflows/validate_input.nf
 *
 *  Checks:
 *    • samplesheet exists and has header: sample,sam
 *    • reference FASTA is non-empty, single-record, annotated
 *    • amplicons TSV has exactly 7 columns
 *  Emits:
 *    • samplesheet_ch  — same path (pass-through)
 *    • reference_ch    — same path (pass-through)
 *    • amplicons_ch    — same path (pass-through)
 * =========================================================
 */

workflow VALIDATE_INPUT {
    take:
    // Channels created from params.* at the call site
    samplesheet_ch  // path (nullable)
    reference_ch    // path (nullable)
    amplicons_ch    // path (nullable)

    main:

    // ── 1. Check samplesheet ──────────────────────────────
    if (samplesheet_ch.isEmpty()) {
        log.error('ERROR: --samplesheet is required. See --help.')
        exit 1
    }

    Channel
        .fromPath(samplesheet_ch, checkIfExists: true)
        .ifEmpty { log.error("Samplesheet not found: ${samplesheet_ch}"); exit 1 }
        .set { ss_path_ch }

    // Parse samplesheet: validate header + at least one data row
    ss_valid_ch = ss_path_ch
        .splitCsv(header: true, sep: ',')
        .map { row ->
            if (!row.containsKey('sample') || !row.containsKey('sam')) {
                log.error("Samplesheet must have columns: sample,sam")
                exit 1
            }
            if (!file(row.sam).exists()) {
                log.error("SAM file not found: ${row.sam}")
                exit 1
            }
            [ row.sample, file(row.sam) ]
        }
        .ifEmpty { log.error('Samplesheet is empty or has no valid rows'); exit 1 }
        .set { sample_sam_ch }   // [sample_id, sam_path]

    // ── 2. Check reference FASTA ──────────────────────────
    if (reference_ch.isEmpty()) {
        log.error('ERROR: --reference is required.')
        exit 1
    }

    Channel
        .fromPath(reference_ch, checkIfExists: true)
        .ifEmpty { log.error("Reference not found: ${reference_ch}"); exit 1 }
        .set { ref_path_ch }

    // Validate FASTA structure: must contain protein annotation header
    ref_valid_ch = ref_path_ch
        .splitFasta(record: [id: true, sequence: true])
        .first()
        .map { rec ->
            if (!rec.id.contains('(') || !rec.id.contains(')')) {
                log.warn("Reference header may lack protein annotation. Expected: '>ID PR(Desc):start-end;RT(...);...'")
            }
            rec.sequence
        }
        .first()     // take only the sequence text (pass reference path forward)
        .map { ref_path_ch }   // emit the path, not the sequence
        .set { reference_validated_ch }

    // ── 3. Check amplicons TSV ───────────────────────────
    if (amplicons_ch.isEmpty()) {
        log.error('ERROR: --amplicons is required.')
        exit 1
    }

    Channel
        .fromPath(amplicons_ch, checkIfExists: true)
        .ifEmpty { log.error("Amplicons file not found: ${amplicons_ch}"); exit 1 }
        .set { amp_path_ch }

    // Validate 7-column TSV format (allow both tab and comma)
    amp_valid_ch = amp_path_ch
        .splitCsv(sep: /\t|,\s*/)
        .first()
        .map { fields ->
            if (fields.size() != 7) {
                log.error("Amplicons file must have 7 columns (label,protein,reference,5p_seq,3p_seq,start,end). Found: ${fields.size()}")
                exit 1
            }
        }
        .map { amp_path_ch }   // emit the path
        .set { amplicons_validated_ch }

    // ── Emit ──────────────────────────────────────────────
    emit:
    samplesheet = ss_path_ch            // path (raw CSV file)
    samples     = sample_sam_ch         // [sample_id, sam_path]
    reference   = reference_validated_ch // path
    amplicons   = amplicons_validated_ch // path
}
