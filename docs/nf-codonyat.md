# nf-codonyat: a Nextflow pipeline for codon-aware amino acid variant typing from viral amplicon sequencing

**Marc Noguera Julian**\* — TODO: complete author list and order

\* Corresponding author — TODO: corresponding author e-mail  
TODO: affiliations

**Keywords:** viral genomics, codon-aware variant calling, Nextflow, amplicon sequencing, HIV drug resistance

> **Draft status.** Items marked **TODO** need information that is not in the repository or in the test runs
> described here (author list, affiliations, benchmarks, data provenance, some citations). All numbers in
> Section 3 come from the bundled test data and the commands listed there.

---

## Abstract

**Background.** Viral deep sequencing enables detection of low-frequency drug-resistance mutations, but most tools operate at the nucleotide level without translating reads into amino acid consequences. We present nf-codonyat, a Nextflow pipeline that wraps the codonyat Python package to perform codon-aware variant typing on viral amplicon NGS data, starting either from raw FASTQ reads or from existing SAM alignments.

**Results.** nf-codonyat takes a samplesheet that lists, per sample, either FASTQ files or a SAM file, together with an annotated reference FASTA and an amplicon definitions table. FASTQ samples are quality-checked with FastQC, trimmed with fastp and aligned with bowtie2; all samples are then filtered on mapping quality and alignment flags with samtools before codonyat produces per-codon variant frequency tables and strand-specific coverage diagnostics. A combined summary table and a MultiQC report are produced for each run. Read-processing steps use nf-core modules; codonyat runs from a pinned conda environment or a container image. The pipeline passes `nextflow lint` under Nextflow 26.04 and is tested with nf-test and GitHub Actions under Docker and Conda.

**Availability.** nf-codonyat is open-source (MIT) at https://github.com/sjoclaudi/nf-codonyat. The codonyat Python package is available at https://github.com/mnoguera/codonyat and on PyPI.

---

## 1. Introduction

Viral populations within a host are highly heterogeneous, often comprising multiple quasispecies at low frequency [TODO: citation]. Detecting these low-frequency variants is important for characterising drug-resistance mutations, immune escape and transmission in viruses such as HIV-1, HCV and SARS-CoV-2 [TODO: citation]. Amplicon sequencing protocols for HIV generate large numbers of short reads that are mapped to a reference genome, producing SAM/BAM alignment files as the primary bioinformatic artefact.

Existing variant-calling tools fall into two broad categories: nucleotide-level callers (e.g. LoFreq, VarScan 2, iVar) that report allele frequencies without codon translation, and protein-level tools that require pre-translated inputs [TODO: citations for LoFreq, VarScan 2, iVar]. Neither category natively reconstructs, read by read, the codon present at each protein position from CIGAR-described alignments while keeping forward- and reverse-strand coverage separate.

The codonyat Python package was developed to address this gap: it parses SAM records using their CIGAR strings to reconstruct the reference-aligned codon at each protein position and aggregates forward- and reverse-strand coverage separately. codonyat is a command-line tool that processes one SAM file at a time; it does not trim or align reads, does not filter alignments on mapping quality (it only skips unmapped reads), and does not schedule or summarise multiple samples.

nf-codonyat wraps codonyat in a Nextflow DSL2 pipeline (Di Tommaso et al., 2017) that provides: (i) input validation; (ii) an optional read pre-processing and alignment path from FASTQ; (iii) a common mapping-quality and flag filter applied before codonyat; (iv) parallel per-sample execution; (v) pinned software environments through Conda and containers; (vi) a combined multi-sample summary table and a MultiQC report; and (vii) automated tests with nf-test.

## 2. Methods

### 2.1 Input files

nf-codonyat requires three input files.

**Samplesheet (CSV).** One row per sample with the columns `sample,fastq_1,fastq_2,sam`. Each row provides **either** FASTQ reads (`fastq_1`, plus `fastq_2` for paired-end data) **or** a SAM file already aligned to the reference, never both:

```
sample,fastq_1,fastq_2,sam
patientA,patientA_R1.fastq.gz,patientA_R2.fastq.gz,
patientB,patientB.fastq.gz,,
patientC,,,/data/aligned/patientC.sam
```

Relative paths are resolved against the folder that contains the samplesheet. The original two-column `sample,sam` format is still accepted.

**Reference FASTA.** A single-sequence FASTA file whose header contains protein annotations in the format `Name(Description):start-end`, separated by semicolons:

```
>K03455|HIVHXB2CG PR(Protease):2253-2549;RT(Reverse Transcriptase):2550-3869;INT(Integrase):4230-5093
<sequence>
```

The annotations define the coordinate system used for codon numbering; the FASTA is parsed with Biopython (Cock et al., 2009). For FASTQ samples, the same FASTA is used to build the bowtie2 index, so both input types share one coordinate system.

**Amplicon definitions (TSV).** A seven-column tab-separated file:

```
label   protein  reference         5p_seq                3p_seq                start  end
Amp_RT  RT       K03455|HIVHXB2CG  CCCATTAGCCCTATTGAGAC  GAAGGTTTCTGCTCCTACTA  2550   3869
```

Each row gives an amplicon label, the protein it targets, the reference name, the 5′ and 3′ primer sequences, and the start and end coordinates on the reference. In codonyat 1.0.1 this file is validated and parsed. Reads are assigned to an amplicon only through an `Amp_<number>` tag in the read name; reads without one are counted under `Amp_NONE`. Primer sequences are not used to trim or mask reads (see Discussion).

### 2.2 Workflow overview

```
FASTQ ─► FastQC (raw reads) ─► fastp ─► bowtie2 --very-sensitive-local ─► sorted BAM ─┐
SAM ──────────────────────────────────────────────────────────────────────────────────┤
                                                                                      ▼
            samtools flagstat ─► samtools view -h -q 20 -F 0x904 ─► samtools flagstat
                                                                                      ▼
                         codonyat-runner ─► per-sample TSV + XML ─► codonyat_summary.tsv
MultiQC: FastQC + fastp + bowtie2 + flagstat (before and after filtering)
```

**Figure 1.** TODO: regenerate the workflow diagram for the FASTQ path. The diagrams currently in `docs/images/` (`pipeline_dag.svg`, `nf-metro.svg`) predate it and show the SAM-only workflow.

### 2.3 Read quality control, trimming and alignment (FASTQ samples)

- **FastQC** (Andrews, 2010) runs on the raw reads only. The trimmed reads are covered by fastp's own before/after report.
- **fastp** (Chen et al., 2018) trims and filters reads with `--qualified_quality_phred 20 --unqualified_percent_limit 40 --length_required 50 --cut_tail --cut_tail_mean_quality 20`; `--detect_adapter_for_pe` is added for paired-end data. Read pairs are **not merged**, because codonyat counts forward- and reverse-strand coverage separately.
- **bowtie2** (Langmead & Salzberg, 2012) builds an index from the reference FASTA and aligns the trimmed reads with `--very-sensitive-local`. The alignments are written as a coordinate-sorted BAM file.

All tool arguments can be changed through pipeline parameters (`--fastp_args`, `--bowtie2_args`). No duplicate-removal step is included. In amplicon data, reads from the same amplicon share start positions, so position-based deduplication would discard genuine coverage.

### 2.4 Alignment filtering (all samples)

codonyat 1.0.1 does not filter alignments on mapping quality or on secondary/supplementary flags; it only skips unmapped reads. nf-codonyat therefore applies one filter to the BAM files from the FASTQ path and to user-supplied SAM files alike, using samtools (Danecek et al., 2021):

```
samtools view -h -q 20 -F 0x904 --output-fmt sam
```

This keeps alignments with mapping quality ≥ 20 and removes unmapped (0x4), secondary (0x100) and supplementary (0x800) records. `samtools flagstat` is run before and after the filter, so the effect of the filter is visible per sample. Both thresholds are parameters (`--min_mapq`, `--exclude_flags`).

### 2.5 CIGAR-aware codon extraction

For each read, codonyat builds a map from reference positions to read positions by walking the CIGAR operations: M, = and X consume both reference and read; I and S consume only the read; D and N consume only the reference and map to a gap; H and P consume neither. For every codon start of the selected protein (from the annotated start coordinate to the end coordinate, in steps of three), codonyat considers each mapped read that spans the position and reads the three bases at that position and the next two. A reference position that falls in a deletion contributes `-`, so a codon deleted in the read is reported as `---`. If a position is not covered by the read's alignment at all, the read is skipped for that codon.

The read's strand is taken from SAM flag bit 16. A numeric suffix `_<n>` at the end of a read name is interpreted as a read multiplicity, so the read counts `n` times. This allows compact, collapsed input. Aligners that keep the instrument read name, such as bowtie2 on Illumina data, do not produce such suffixes.

### 2.6 Strand coverage, strand ratio and entropy

For each codon position, codonyat records the forward-strand depth (FWCOV), reverse-strand depth (RVCOV), total depth (TOTALCOV), and the count of each observed codon on each strand. The output table reports each codon's frequency (FREQ, percentage of total depth) and the position-level strand ratio RATIO = FWCOV / RVCOV.

Internally, codonyat also computes:
- a per-codon strand ratio (forward frequency divided by reverse frequency), compared with a window `[ratio_lower, ratio_upper]` (defaults 0.316 and 3.162, i.e. a 10-fold range in either direction);
- the Shannon entropy of the codon distribution at each position, `H(p) = −Σ_c p_c ln(p_c)`, compared with `--entropy_threshold` (default 0.0).

In codonyat 1.0.1 these two flags are not used to remove rows from the TSV or XML output. Every observed codon is reported, and strand balance can be assessed from FWCOV, RVCOV and RATIO. nf-codonyat passes the thresholds through to codonyat (`--ratio_upper`, `--ratio_lower`, `--entropy_threshold`).

### 2.7 Pipeline implementation

nf-codonyat is written in Nextflow DSL2 strict syntax and consists of:

- **`VALIDATE_INPUT` (subworkflow).** Checks that the samplesheet exists and that each row has a sample and either FASTQ or SAM (not both); that every referenced file exists; that the reference looks like a FASTA file and its header annotates the selected `--protein` (a header without any annotations only triggers a warning); and that the amplicons TSV has seven columns. Emits separate FASTQ and SAM channels.
- **nf-core modules** (Ewels et al., 2020), installed with nf-core tools and tracked in `modules.json`: `fastqc`, `fastp`, `bowtie2/build`, `bowtie2/align`, `samtools/view`, `samtools/flagstat` (used twice, before and after filtering) and `multiqc`.
- **`CODONYAT_RUN` (local module).** One task per sample. It links the filtered alignment as `<sample>.sam`, so the FILE column always shows the sample ID, and runs:

  ```
  codonyat-runner <sample>.sam <ref.fasta> <amplicons.tsv> \
      --protein RT --ratio-upper 3.162 --ratio-lower 0.316 --entropy-threshold 0.0 \
      --csv-path <sample>.tsv --xml-path <sample>.xml
  ```

- **`CODONYAT_SUMMARY` (local module).** Merges all per-sample TSV files into `codonyat_summary.tsv`, adding a `SAMPLE` column.
- **MultiQC** (Ewels et al., 2016). Collects the FastQC, fastp, bowtie2 and flagstat outputs into one report.

Outputs are published to `samples/<sample>/` (TSV, XML), `fastqc/`, `fastp/`, `alignment/` (BAM, bowtie2 logs, flagstat), `multiqc/`, `codonyat_summary.tsv`, and `pipeline_info/` (Nextflow execution report, timeline, trace and DAG).

### 2.8 Software packaging and execution environments

- **codonyat steps** (`CODONYAT_RUN`, `CODONYAT_SUMMARY`) use codonyat 1.0.1 and Biopython 1.85 from either:
  - a conda environment file (`modules/local/codonyat/run/environment.yml`: conda-forge Python 3.12 and Biopython 1.85, codonyat 1.0.1 via pip); or
  - the container image `ghcr.io/sjoclaudi/nf-codonyat:0.1.0`, built from the repository's `Dockerfile` (python:3.12-slim with the same versions). The CI workflow publishes this image on pushes to `main`. TODO: confirm the image is published and public before submission.
- **nf-core modules** bring their own BioContainers images and conda environments: FastQC 0.12.1, fastp 1.3.6, bowtie2 2.5.4 (with samtools 1.21 for sorting), samtools 1.24 and MultiQC 1.35.
- **Profiles:** `docker`, `conda`, `mamba` and `singularity`, plus a `test` profile with the bundled data. The docker and conda profiles are tested (Section 3). The singularity and mamba profiles are defined but have not been tested.
- **Nextflow compatibility:** the manifest requires Nextflow ≥ 25.04. The pipeline uses the strict syntax, passes `nextflow lint` with no errors, and was tested with Nextflow 26.04.6 on Java 21. Only the local executor has been tested. TODO: HPC/cloud execution, if it is to be claimed.

### 2.9 Testing and continuous integration

The nf-test suite (Forer & Schönherr, 2025) runs the whole pipeline and has six tests:

1. The test profile data (two synthetic SAM samples and one real FASTQ pair) produces per-sample TSV/XML, the expected FastQC, fastp, BAM, bowtie2 log, flagstat and MultiQC outputs, and a summary with rows for all three samples. The test also checks the expected frequencies of the spiked-in mutations and snapshots the md5 sums of the summary and per-sample outputs.
2. An old-style `sample,sam` samplesheet still works.
3. A samplesheet row with both FASTQ and SAM is rejected with a clear message.
4. A missing `--samplesheet` is rejected with a clear message.
5. A `--protein` not annotated in the reference is rejected.
6. A config passed with `-c` that changes `outdir` produces a warning, and the run still succeeds.

GitHub Actions runs `nextflow lint .` and then, for both the `docker` and `conda` profiles, the nf-test suite and a full `-profile test` run with checks on the summary, FASTQ-path and MultiQC outputs.

## 3. Results

### 3.1 Synthetic SAM test data

The two SAM test samples are generated by `assets/testdata/make_testdata.py` from HXB2 (GenBank K03455). They contain exact copies of two RT amplicon regions (HXB2 2550–2789 and 2997–3149), with known mutations spiked in.

- **sample1** carries M41L, K65R and M184V with balanced strands.
- **sample2** is wild type, plus a forward-strand-only K65R artefact and a read with a deletion of codon 69.

The pipeline reports these frequencies:

| Sample | Mutation | HXB2 position | Codon | FREQ (%) |
|--------|----------|---------------|-------|----------|
| sample1 | M41L | 2670 | CTG | 24.528 |
| sample1 | K65R | 2742 | AGA | 9.434 |
| sample1 | M184V | 3099 | GTG | 50.0 |
| sample2 | T69 deletion | 2754 | `---` | 8.163 |
| sample2 | (wild type at 184) | 3099 | GTG | not observed |

The mapping-quality and flag filter (Section 2.4) leaves these outputs unchanged: the per-sample TSV and XML files are byte-identical (same md5) to those produced before the filter was added.

### 3.2 FASTQ path on a real HIV-1 amplicon library (HVG286PL subset)

The FASTQ test data contains 2,000 read pairs randomly subsampled (`seqtk sample -s42`) from a paired-end HIV-1 pol amplicon library, HVG286PL (Illumina reads of up to 301 bp). TODO: describe the sample origin, library preparation and sequencing run, ethics/consent, and the public accession, if any.

The data were run with `-profile test,docker` and the default parameters, aligned to HXB2 with the `Amp_RT` amplicon (HXB2 2550–3869, the RT annotation of the reference):

| Step | Result |
|------|--------|
| Input | 4,000 reads (2,000 pairs) |
| fastp | 3,866 reads passed (96.65%); removed: 114 low quality, 16 too short, 4 too many N |
| bowtie2 `--very-sensitive-local` | 98.27% overall alignment rate (3,799 of 3,866 reads mapped) |
| samtools view `-q 20 -F 0x904` | 3,767 alignments kept |
| codonyat | 2,300 codon rows covering all 440 RT codon positions (HXB2 2550–3867) |

At the first RT codon (HXB2 2550) the majority codon is CCC (96.918%, total depth 292), as expected for proline 1 of RT. TODO: interpretation of the variants observed in this sample, if wanted.

### 3.3 Reproducibility across environments

On the bundled test data, the docker and conda profiles produced identical outputs: the same `codonyat_summary.tsv` md5 from `-profile test,docker` and `-profile test,conda`, and both nf-test runs (`--profile docker` and `--profile conda`) matched the same snapshot. All six nf-test tests passed in both environments, locally and in GitHub Actions. Singularity was not tested.

### 3.4 Performance

TODO: benchmark (runtime and memory per sample, scaling with read depth and number of samples) on full-size datasets. No benchmark has been run; the test runs above are too small to be informative.

## 4. Discussion

nf-codonyat now covers the path from raw amplicon reads to codon-level variant tables, while still accepting existing SAM alignments from any aligner. Both input types go through the same mapping-quality and flag filter before codonyat. This matters because codonyat itself only skips unmapped reads: without the filter, low-confidence, secondary and supplementary alignments would be counted.

The FASTQ path uses widely used tools (FastQC, fastp, bowtie2, samtools, MultiQC) through nf-core modules, so tool versions and containers are pinned and can be updated with standard nf-core tooling. Local alignment (`--very-sensitive-local`) allows soft-clipping of read ends that do not match the reference. TODO: justify the choice for divergent viral samples with data or citation, if wanted.

The default strand-ratio window of 0.316–3.162 (10-fold asymmetry) mirrors the defaults of the earlier Perl implementation that codonyat replaces. Users working with other viral systems may need to adjust these thresholds; nf-codonyat exposes them as parameters. In codonyat 1.0.1 the ratio and entropy thresholds are computed but do not filter the reported rows (Section 2.6).

**Limitations and future options.**
- **Primer clipping** is not performed. Bases under primer-binding sites reflect the primer rather than the template, so variants in primer regions should be interpreted with care. Primer clipping (for example with `ivar trim` or `samtools ampliconclip` and a primer BED file) is a future option.
- **Variant effect prediction** beyond codon translation is out of scope.
- **Consensus or haplotype reconstruction** is out of scope.
- Only one protein is analysed per run (`--protein`).
- Only the local executor and the docker and conda profiles have been tested.

## 5. Conclusion

nf-codonyat brings the codon-aware variant typing of the codonyat Python package into a Nextflow pipeline that accepts raw FASTQ reads or SAM alignments. It applies a common alignment filter, produces per-sample and combined codon tables with a MultiQC report, and is tested with nf-test under Docker and Conda. It is freely available under the MIT licence.

Future development may include primer clipping, multi-protein analysis per run, and validation on larger datasets (TODO).

## 6. Data and software availability

- **nf-codonyat pipeline**: https://github.com/sjoclaudi/nf-codonyat (MIT licence). TODO: release tag/DOI for the version described here.
- **codonyat Python package**: https://github.com/mnoguera/codonyat; PyPI `codonyat` 1.0.1.
- **Container image**: `ghcr.io/sjoclaudi/nf-codonyat:0.1.0` (TODO: confirm public availability).
- **Test data**: `assets/testdata/` of the pipeline repository (synthetic SAM files, HVG286PL FASTQ subset, HXB2 reference, amplicon definitions).

## 7. Acknowledgements

TODO

## 8. References

Andrews S. FastQC: a quality control tool for high throughput sequence data. 2010. https://www.bioinformatics.babraham.ac.uk/projects/fastqc/

Chen S, Zhou Y, Chen Y, Gu J. fastp: an ultra-fast all-in-one FASTQ preprocessor. *Bioinformatics*. 2018;34(17):i884-i890. doi:10.1093/bioinformatics/bty560

Cock PJA, Antao T, Chang JT, et al. Biopython: freely available Python tools for computational molecular biology and bioinformatics. *Bioinformatics*. 2009;25(11):1422-1423. doi:10.1093/bioinformatics/btp163

Danecek P, Bonfield JK, Liddle J, et al. Twelve years of SAMtools and BCFtools. *GigaScience*. 2021;10(2):giab008. doi:10.1093/gigascience/giab008

Di Tommaso P, Chatzou M, Floden EW, Barja PP, Palumbo E, Notredame C. Nextflow enables reproducible computational workflows. *Nat Biotechnol*. 2017;35(4):316-319. doi:10.1038/nbt.3820

Ewels P, Magnusson M, Lundin S, Käller M. MultiQC: summarize analysis results for multiple tools and samples in a single report. *Bioinformatics*. 2016;32(19):3047-3048. doi:10.1093/bioinformatics/btw354

Ewels PA, Peltzer A, Fillinger S, et al. The nf-core framework for community-curated bioinformatics pipelines. *Nat Biotechnol*. 2020;38(3):276-278. doi:10.1038/s41587-020-0439-x

Forer L, Schönherr S. Improving the reliability, quality, and maintainability of bioinformatics pipelines with nf-test. *GigaScience*. 2025;14:giaf130. doi:10.1093/gigascience/giaf130

Langmead B, Salzberg SL. Fast gapped-read alignment with Bowtie 2. *Nat Methods*. 2012;9(4):357-359. doi:10.1038/nmeth.1923

TODO: references for intra-host viral diversity and low-frequency variant detection (Introduction), and for LoFreq, VarScan 2 and iVar. Three references in the previous draft could not be verified and were removed: "Simmonds et al. 2019, Nat Rev Microbiol, doi:10.1038/s41579-018-0128-7", "Zadeh et al. 2021, Viruses 13(2):195" and "Lamprecht et al. 2020, F1000Res 9:33". nf-test is now cited from its GigaScience paper.
