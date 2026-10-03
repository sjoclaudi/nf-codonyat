/*
 * =========================================================
 *  subworkflows/validate_input.nf
 *
 *  Checks:
 *    • samplesheet exists; each row has a sample and either FASTQ
 *      (fastq_1, optional fastq_2) or a SAM; every file exists
 *      (relative paths are resolved against the samplesheet's folder)
 *    • reference FASTA header carries protein annotations, including the
 *      requested --protein
 *    • amplicons TSV has 7 tab-separated columns
 *
 *  Any failed check stops the run with a clear error message.
 *
 *  Emits:
 *    fastq     — queue channel of [ meta, [ fastq_1, (fastq_2) ] ]
 *    sam       — queue channel of [ meta, sam ]
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
    // Columns: sample, and either fastq_1 (+ optional fastq_2) or sam.
    // A sheet with only sample,sam (the original format) still works.
    def ss_file = file(samplesheet_path, checkIfExists: true)

    rows_ch = channel
        .fromPath(ss_file)
        .splitCsv(header: true, sep: ',')
        .map { row ->
            def sample = row.sample?.trim()
            def fq1    = row.fastq_1?.trim()
            def fq2    = row.fastq_2?.trim()
            def sam    = row.sam?.trim()
            if (!sample) {
                error "Samplesheet ${ss_file}: every row needs a 'sample' value (offending row: ${row})"
            }
            if (!fq1 == !sam) {
                error "Samplesheet ${ss_file}: sample '${sample}' must have either fastq_1 or sam (not both, not neither)"
            }
            if (fq2 && !fq1) {
                error "Samplesheet ${ss_file}: sample '${sample}' has fastq_2 but no fastq_1"
            }
            sam
                ? tuple([id: sample], 'sam', [resolveSheetPath(ss_file, sample, sam)])
                : tuple([id: sample, single_end: !fq2], 'fastq', fq2 ? [resolveSheetPath(ss_file, sample, fq1), resolveSheetPath(ss_file, sample, fq2)] : [resolveSheetPath(ss_file, sample, fq1)])
        }

    fastq_ch = rows_ch
        .filter { _meta, type, _files -> type == 'fastq' }
        .map { meta, _type, files -> tuple(meta, files) }

    sam_ch = rows_ch
        .filter { _meta, type, _files -> type == 'sam' }
        .map { meta, _type, files -> tuple(meta, files[0]) }

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
    fastq     = fastq_ch       // [ meta, [ fastq_1, (fastq_2) ] ]
    sam       = sam_ch         // [ meta, sam ]
    reference = reference_ch
    amplicons = amplicons_ch
}

// Relative paths in the samplesheet are resolved against its folder
def resolveSheetPath(sheet, String sample, String p) {
    def f = p.contains('://') || p.startsWith('/') ? file(p) : sheet.parent.resolve(p)
    if (!f.exists()) {
        error "File for sample '${sample}' not found: ${f}"
    }
    return f
}
