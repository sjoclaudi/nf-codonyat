# Task image for the local nf-codonyat processes (codonyat and the helper
# scripts in bin/). Nextflow itself runs on the host; this image only carries
# the tools. Third-party steps use the nf-core module containers.
# Keep versions in sync with modules/local/codonyat/run/environment.yml.
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/sjoclaudi/nf-codonyat"
LABEL org.opencontainers.image.description="codonyat 1.1.0 runtime for the nf-codonyat Nextflow pipeline (research use only)"
LABEL org.opencontainers.image.licenses="MIT"

# procps provides `ps`, which Nextflow uses to collect task metrics
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

# codonyat 1.1.0 (streaming, multi-protein) is not on PyPI yet; install the
# reviewed source at a pinned commit until it is released.
ARG CODONYAT_SRC=https://github.com/sjoclaudi/codonyat-1/archive/602b16c916bd5b4e5eeb930d9acbddd8c9d9bcd1.tar.gz
RUN pip install --no-cache-dir "biopython==1.85" "codonyat @ ${CODONYAT_SRC}"

CMD ["codonyat-runner", "--help"]
