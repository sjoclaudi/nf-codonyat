/*
 * =========================================================
 *  subworkflows/validate_input.nf
 *
 *  Checks:
 *    • samplesheet exists, has columns sample,sam and every SAM exists
 *      (relative SAM paths are resolved against the samplesheet's folder)
 *    • reference FASTA header carries protein annotations, including the
 *      requested --protein
 *    • amplicons TSV has 7 tab-separated columns
 *
 *  Any failed check stops the run with a clear error message.
 *
 *  Emits:
 *    samples   — queue channel of [ val(sample_id), path(sam) ]
 *    reference — value channel: path to the reference FASTA
 *    amplicons — value channel: path to the amplicons TSV
 * =========================================================
 */

workflow VALIDATE_INPUT {
    take:
    samplesheet_path  // String
    reference_path    // String
    amplicons_path    // String

    main:

    // ── 1. Samplesheet ────────────────────────────────────
    def ss_file = file(samplesheet_path, checkIfExists: true)

    samples_ch = channel
        .fromPath(ss_file)
        .splitCsv(header: true, sep: ',')
        .map { row ->
            if (!row.sample || !row.sam) {
                error "Samplesheet ${ss_file} must have non-empty columns 'sample,sam' (offending row: ${row})"
            }
            def sam = row.sam.contains('://') || row.sam.startsWith('/')
                ? file(row.sam)
                : ss_file.parent.resolve(row.sam)
            if (!sam.exists()) {
                error "SAM file for sample '${row.sample}' not found: ${sam}"
            }
            tuple(row.sample, sam)
        }

    // ── 2. Reference FASTA ────────────────────────────────
    // Value channel so it is reused for every sample
    def ref_file = file(reference_path, checkIfExists: true)
    def header = ref_file.withReader { reader -> reader.readLine() } ?: ''
    if (!header.startsWith('>')) {
        error "Reference ${ref_file} does not look like a FASTA file"
    }
    def proteins = (header =~ /(\w+)\([^)]*\):\d+-\d+/).collect { m -> m[1] }
    if (!proteins) {
        log.warn "Reference header lacks protein annotations. Expected format: '>ID PR(Protease):2253-2549;RT(Reverse Transcriptase):2550-3869'"
    }
    else if (!(params.protein in proteins)) {
        error "Reference header has no annotation for --protein ${params.protein} (found: ${proteins.join(', ')})"
    }
    reference_ch = channel.value(ref_file)

    // ── 3. Amplicons TSV ──────────────────────────────────
    def amp_file = file(amplicons_path, checkIfExists: true)
    def ampHeader = amp_file.withReader { reader -> reader.readLine() } ?: ''
    def nCols = ampHeader.split('\t').size()
    if (nCols != 7) {
        error "Amplicons file ${amp_file} must have 7 tab-separated columns " +
              "(label,protein,reference,5p_seq,3p_seq,start,end); found ${nCols}"
    }
    amplicons_ch = channel.value(amp_file)

    emit:
    samples   = samples_ch
    reference = reference_ch
    amplicons = amplicons_ch
}
