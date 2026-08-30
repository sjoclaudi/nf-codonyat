/*
 * =========================================================
 *  modules/codonyat/run/main.nf
 *
 *  Process: CODONYAT_RUN
 *
 *  Wraps:  codonyat-runner <sam> <ref.fasta> <amplicons.tsv>
 *          [--protein STR]
 *          [--ratio-upper FLOAT]
 *          [--ratio-lower FLOAT]
 *          [--entropy-threshold FLOAT]
 *          [--csv-path PATH]
 *          [--xml-path PATH]
 *
 *  Input  : tuple val(sample_id), path(sam), path(reference), path(amplicons)
 *  Output : tuple val(sample_id), path(tsv), path(xml)
 * =========================================================
 */

process CODONYAT_RUN {
    tag "CODONYAT_RUN ${sample_id}"

    label 'process_medium'

    // Install codonyat from PyPI (or replace with git+https once on GitHub)
    // Using conda/biopython as base, then pip install codonyat
    conda 'bioconda::biopython>=1.79'

    input:
    tuple val(sample_id), path(sam)
    path reference
    path amplicons

    output:
    tuple val(sample_id), path("${sample_id}.tsv"), path("${sample_id}.xml"), emit: results

    shell:
    '''
    set -euo pipefail

    # Ensure codonyat-runner is available
    if ! command -v codonyat-runner &>/dev/null; then
        echo "Installing codonyat..." >&2
        pip install --quiet codonyat
    fi

    codonyat-runner "!{sam}" \
        "!{reference}" \
        "!{amplicons}" \
        --protein "!{params.protein}" \
        --ratio-upper "!{params.ratio_upper}" \
        --ratio-lower "!{params.ratio_lower}" \
        --entropy-threshold "!{params.entropy_threshold}" \
        --csv-path "!{sample_id}.tsv" \
        --xml-path  "!{sample_id}.xml"

    # Rename output files to sample_id prefix (codonyat-runner uses input filename stem)
    for f in *.tsv *.xml; do
        [ -e "$f" ] || continue
        base=$(basename "$f")
        stem="!{sample_id}"
        case "$base" in
            *.tsv)  [ "$base" != "${stem}.tsv" ] && mv "$base" "${stem}.tsv" ;;
            *.xml)  [ "$base" != "${stem}.xml" ] && mv "$base" "${stem}.xml"  ;;
        esac
    done

    echo "Done: ${sample_id}" >&2
    '''
}
