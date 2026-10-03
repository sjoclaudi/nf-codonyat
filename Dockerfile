# Task image for nf-codonyat processes (CODONYAT_RUN, CODONYAT_SUMMARY).
# Nextflow itself runs on the host; this image only carries the tools.
# Keep versions in sync with modules/local/codonyat/run/environment.yml.
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/sjoclaudi/nf-codonyat"
LABEL org.opencontainers.image.description="codonyat 1.0.1 runtime for the nf-codonyat Nextflow pipeline"
LABEL org.opencontainers.image.licenses="MIT"

# procps provides `ps`, which Nextflow uses to collect task metrics
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "biopython==1.85" "codonyat==1.0.1"

CMD ["codonyat-runner", "--help"]
