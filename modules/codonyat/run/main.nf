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

    // Install codonyat Python package (published on PyPI).
    // biopython is the only runtime dependency.
    conda 'bioconda::biopython>=1.79'
    // Also make codonyat available via pip when using docker/singularity
    // (conda env has biopython; codonyat itself is pip-installed below)

    input:
    tuple val(sample_id), path(sam)
    path reference
    path amplicons

    output:
    tuple val(sample_id), path("${sample_id}.tsv"), path("${sample_id}.xml"), emit: results

    shell:
    '''
    set -euo pipefail

    # Install codonyat from PyPI (required when using conda profile;
    # docker image bundles it via Dockerfile)
    pip install --quiet codonyat

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
