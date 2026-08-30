FROM python:3.11-slim

LABEL maintainer="Marc Noguera Julian <sjoclaudi@gmail.com>"
LABEL description="nf-codonyat: codon-aware amino acid variant typing"

# Install Nextflow, Java, and pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless curl git \
    && rm -rf /var/lib/apt/lists/*

# Install Nextflow
RUN curl -s https://get.nextflow.io | bash \
    && mv nextflow /usr/local/bin/

# Install biopython (runtime dep of codonyat)
RUN pip install --no-cache-dir biopython>=1.79

# Install codonyat from PyPI
RUN pip install --no-cache-dir codonyat

WORKDIR /workspace

# Copy pipeline files
COPY . /workspace/

ENV NXF_ANSI_LOG=false
