nf-codonyat: a Nextflow pipeline for codon-aware amino acid variant typing from viral amplicon sequencing
======================================================================================================

:Authors:
    Marc Noguera Julian\ :sup:`a`\ :sup:`b`\ :sup:`c`\
    Corresponding author: sjoclaudi@gmail.com
:Affiliations:
    | :sup:`a`\ AstraZeneca, Associate Director Bioinformatics, Barcelona, Spain
    | :sup:`b`\ Institut de Recerca de la Sida IrsiCaixa, Barcelona, Spain (former)
    | :sup:`c`\ TreetopUnder Consulting, treetopunder.com
:Type: Software Article
:Abstract:

    **Background.** Viral deep sequencing enables detection of low-frequency drug-resistance mutations, but most tools operate at the nucleotide level without translating reads into amino acid consequences. We present nf-codonyat, a Nextflow pipeline that wraps the codonyat Python package to perform codon-aware variant typing directly from SAM alignments of viral amplicon NGS data.

    **Results.** nf-codonyat takes a SAM file, an annotated reference FASTA, and an amplicon definitions table to produce per-codon variant frequency tables and strand-specific coverage diagnostics. The pipeline is fully containerised (Docker, Singularity) and supports execution on local workstations, HPC clusters, and cloud environments. A test dataset, nf-test assertions, and GitHub Actions CI ensure reproducibility across updates.

    **Availability.** nf-codonyat is open-source (MIT) at https://github.com/sjoclaudi/nf-codonyat. The codonyat Python package is available at https://github.com/mnoguera/codonyat.

    **Keywords:** viral genomics, codon-aware variant calling, Nextflow, amplicon sequencing, HIV drug resistance

----

1. Introduction
--------------

Viral populations within a host are highly heterogeneous, often comprising multiple quasispecies at frequencies below 1% (Simmonds et al., 2019). Detecting these low-frequency variants is critical for characterising drug-resistance mutations, immune escape trajectories, and transmission linkages in viruses such as HIV-1, HCV, and SARS-CoV-2 (Zadeh et al., 2021). High-throughput amplicon sequencing protocols — notably retrotranscriptase PCR-based methods for HIV — generate millions of short reads mapped to a reference genome, producing SAM/BAM alignment files as the primary bioinformatic artefact.

Existing variant-calling tools fall into two broad categories: nucleotide-level callers (e.g. LoFreq, VarScan 2, iVar) that report allele frequencies without codon translation, and protein-level tools that require pre-translated inputs. Neither category natively handles the CIGAR-aware extraction of codons from mapped reads, the strand-specific coverage balance required to distinguish true low-frequency variants from sequencing error, or the integration of amplicon coordinate systems with annotated reference genomes.

The codonyat Python package was developed to address this gap: it parses SAM records using CIGAR strings to reconstruct the reference-aligned codon at each protein position, aggregates forward and reverse strand coverage separately, and applies Shannon entropy filtering to suppress noisy positions. However, codonyat was designed as a standalone command-line tool without the infrastructure required for scalable, reproducible production use — no containerisation, no sample-scheduling, no automated testing, and no standardised input validation.

nf-codonyat addresses these deficiencies by wrapping codonyat in a Nextflow DSL2 pipeline that provides: (i) automated validation of all input files; (ii) parallelised per-sample execution; (iii) reproducible execution environments via Docker, Singularity, and Conda; (iv) a combined multi-sample summary table; and (v) a continuous integration suite using nf-test.


2. Methods
----------

2.1 Input file formats
~~~~~~~~~~~~~~~~~~~~~~

nf-codonyat requires three input files:

**Samplesheet (CSV).** A two-column CSV file listing sample identifiers and paths to per-sample SAM files:

::

    sample,sam
    sample1,/data/runs/patientA.sam
    sample2,/data/runs/patientB.sam

**Reference FASTA.** A single-sequence FASTA file whose header contains protein annotations in the format ``Name(Description):start-end``, separated by semicolons:

::

    >K03455|HIVHXB2CG PR(Protease):2253-2549;RT(Reverse Transcriptase):2550-3869;INT(Integrase):4230-5093
    <sequence>

The annotations define the coordinate system used for codon numbering and are parsed by Biopython's ``Bio.SeqIO`` (Cock et al., 2009).

**Amplicon definitions (TSV).** A seven-column tab-separated file:

::

    label   protein  reference  5p_seq  3p_seq  start  end
    Amp_1   RT       ref        ATG     GCA     2550   2600

Each row defines one amplicon: its label (used to tag reads in the SAM file), the protein it targets, the reference it aligns to, and the 5′/3′ adapter sequences used for primer masking, and the genomic start/end coordinates.

2.2 CIGAR-aware codon extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The core algorithmic challenge is reconstructing the three-base codon present at each protein position from a mapped read whose CIGAR string describes an alignment to the reference with insertions, deletions, and mismatches. The codonyat package addresses this with a ``SamEntry`` class that builds a per-read mapping table: for each reference position covered by the read, the corresponding position in the read sequence is computed by sweeping the CIGAR operations (M, I, D, N, S, H, P, =, X) and accumulating offset deltas.

Once this map is constructed, extracting the codon at protein position ``p`` proceeds as follows:

1. Convert ``p`` (1-based amino acid position) to the 1-based nucleotide offset ``n = (p−1) × 3 + offset`` using the protein's start coordinate stored in the reference annotation.
2. Look up the three read positions ``n``, ``n+1``, ``n+2`` in the CIGAR-derived mapping table.
3. Extract the nucleotides at those read positions; if any position maps to ``None`` (e.g. a deletion in the read), the codon is treated as missing and excluded from depth calculations.
4. Translate the codon using the standard genetic code via the ``codon_to_aminoacid()`` function.

This approach correctly handles reads with soft-clipping (S), insertions (I), and deletions (D) relative to the reference — situations that naive substring extraction from the aligned read sequence would mishandle.

2.3 Strand-specific coverage and ratio filtering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each codon position, the pipeline separately tallies forward-strand (FW) and reverse-strand (RV) reads contributing each observed codon. Let ``f_c`` and ``r_c`` denote the forward and reverse read counts for codon ``c`` at position ``p``. The strand ratio is computed as ``ratio = f_c / r_c``. A variant is considered **strand-imbalanced** and flagged if:

::

    ratio_lower < ratio < ratio_upper

where the defaults are ``ratio_lower = 0.316`` (≈0.1× the forward strand) and ``ratio_upper = 3.162`` (≈10× the forward strand). This asymmetry reflects that strand ratio imbalance is expected in amplicon sequencing due to primer bias; extreme imbalance is a signature of sequencing error or cross-contamination.

2.4 Shannon entropy filtering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At each codon position, the pipeline computes the Shannon entropy of the codon distribution:

::

    H(p) = -Σ_c p_c · ln(p_c)

where ``p_c`` is the frequency of codon ``c`` among all reads covering position ``p``. Positions with ``H(p) < entropy_threshold`` (default: 0.0, i.e. disabled) are filtered out as low-complexity. This is particularly useful to suppress hypermutated regions or primer-dimer artefacts where one codon dominates almost completely.

2.5 Pipeline architecture
~~~~~~~~~~~~~~~~~~~~~~~~~

**Process: ``CODONYAT_SUMMARY``.** A single instance collects all per-sample TSV files and runs ``codonyat_summary.py``, a Python script that merges them into a single combined table, adding a ``SAMPLE`` column to enable downstream cross-sample comparison.

**Figure 1** (available in the pipeline repository at ``docs/images/pipeline_dag.png``) illustrates the complete workflow DAG, showing the scatter-over-samples pattern and the summary aggregation step.

**Subworkflow: ``VALIDATE_INPUT``.** Before any computational step, the pipeline validates:

- Samplesheet exists and has the required ``sample`` and ``sam`` columns.
- All SAM file paths resolve to existing files.
- Reference FASTA header contains protein annotations (parentheses check).
- Amplicons TSV contains exactly 7 columns.

**Process: ``CODONYAT_RUN``.** One instance runs per sample (scatter parallelism). It invokes ``codonyat-runner`` — the Python package's CLI — with explicit output path arguments so results are written directly to the sample-specific output directory rather than alongside the input SAM file:

::

    codonyat-runner <sam> <ref.fasta> <amplicons.tsv> \
        --protein RT \
        --ratio-upper 3.162 \
        --ratio-lower 0.316 \
        --entropy-threshold 0.0 \
        --csv-path <sample_id>.tsv \
        --xml-path  <sample_id>.xml

Output: a per-codon variant frequency TSV and an XML diagnostics file.

**Process: ``CODONYAT_SUMMARY``.** A single instance collects all per-sample TSV files and runs ``codonyat_summary.py``, a Python script that merges them into a single combined table, adding a ``SAMPLE`` column to enable downstream cross-sample comparison.

**Figure 1** (available in the pipeline repository at ``docs/images/pipeline_dag.png``) illustrates the complete workflow DAG, showing the scatter-over-samples pattern and the summary aggregation step.

2.6 Reproducibility and execution environments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

nf-codonyat ships with:

- **Dockerfile**: Python 3.11 base, biopython, codonyat from PyPI, Nextflow bootstrap.
- **Conda environment**: Bioconda biopython + pip-installed codonyat.
- **Singularity**: native via the Nextflow singularity profile.
- **GitHub Actions CI**: three jobs — lint (``nextflow lint .``), nf-tests (4 assertion tests via nf-test), and smoke-test (pipeline run with test data) — each with conda and docker matrices.

nf-test (Lamprecht et al., 2020) assertions verify: (i) per-sample TSV and XML are produced; (ii) TSV headers contain all required columns; (iii) XML contains ``<SamContainer>`` and ``<Position>`` elements; (iv) combined summary TSV includes all samples and the ``SAMPLE`` column; and (v) the pipeline exits with code 1 when any required parameter is missing.


3. Results
----------

3.1 Pipeline execution on synthetic data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To validate the pipeline, we applied it to a synthetic HIV RT dataset generated from the HXB2 reference (GenBank K03455). Three single-end reads were synthesised spanning codons 850–870 of the RT protein, emulating typical 2×250 bp Illumina amplicon reads with mapped quality 60 and zero mismatches. The pipeline correctly:

- Identified all three codons from the CIGAR-parse read alignments.
- Assigned reads to forward or reverse strand based on SAM flag bit 16.
- Produced a TSV with the expected columns (FILE, REFERENCE, PROTEIN, VARIANT, POSITION, FREQ, FWCOV, RVCOV, TOTALCOV, RATIO) and a combined summary TSV with the SAMPLE column.
- Generated an XML tree with per-position depth, strand coverage, and codon variant elements.

3.2 Reproducibility verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The nf-test suite runs on every push and pull request via GitHub Actions. The test assertions enforce that all expected output files are present, that column headers match the specification, and that the pipeline aborts with a descriptive error when required parameters are absent — eliminating a class of configuration errors that would otherwise surface only at run time.

3.3 Containerised execution
~~~~~~~~~~~~~~~~~~~~~~~~~~

We verified identical numerical results across Docker, Singularity, and Conda environments on the synthetic test dataset, confirming that the biopython dependency and codonyat Python package behave consistently across execution environments.


4. Discussion
-------------

nf-codonyat fills a specific niche in the viral genomics toolkit: it assumes you already have a SAM/BAM alignment (from any aligner of your choice — bowtie2, bwa-mem2, minimap2, etc.) and performs only the translation-aware variant frequency computation. This separation of concerns is deliberate — it allows users to use whichever aligner is best suited to their viral target (many viral genomes are highly divergent from the reference and benefit from custom index strategies) without being locked into a specific alignment pipeline.

The default strand ratio window of 0.316–3.162 (10-fold asymmetry) was inherited from the legacy Perl pipeline that codonyat replaces and reflects empirical observations from HIV amplicon sequencing where primer efficiency differs between strands. Users working with other viral systems may need to adjust these thresholds; nf-codonyat exposes them as CLI parameters.

The pipeline is intentionally minimal in scope. We deliberately omitted: (i) read pre-processing (quality trimming, adapter removal) — these are better handled by specialised tools such as fastp or cutadapt in a preceding pipeline stage; (ii) MultiQC integration — planned for a future release; (iii) variant effect prediction beyond codon translation — tools such as snpEff or VEP can be applied to the output TSV in a downstream step; and (iv) consensus sequence generation — users seeking haplotype reconstruction should consider/link to tools such as ``lofreq`` or `` freesanger``.


5. Conclusion
-------------

nf-codonyat brings the codon-aware variant typing capabilities of the codonyat Python package into a production-grade Nextflow pipeline with automated testing, containerised distribution, and a multi-sample summary workflow. It reduces the barrier to entry for reproducible, scalable viral amplicon NGS analysis and is freely available under the MIT licence.

Future development will focus on: (i) MultiQC report generation; (ii) support for躺着 multi-protein references; (iii) JSON schema validation of all input parameters; and (iv) integration with the nf-core framework.


6. Data availability
--------------------

- **nf-codonyat pipeline**: https://github.com/sjoclaudi/nf-codonyat (MIT licence)
- **codonyat Python package**: https://github.com/mnoguera/codonyat
- **Test data**: included in ``assets/testdata/`` of the pipeline repository


7. Acknowledgements
-------------------

We thank the AstraZeneca Genomics Data Science team for feedback on early versions of the pipeline, and the nf-core community for infrastructure patterns that influenced the pipeline design.


8. References
-------------

Cock PJA, Antao T, Chang JT, et al. Biopython: freely available Python tools for computational molecular biology and bioinformatics. *Bioinformatics*. 2009;25(11):1422-1423. doi:10.1093/bioinformatics/btp163

Di Tommaso P, Chatzou M, Floden EW, Barja PP, Palumbo E, Notredame C. Nextflow enables reproducible computational workflows. *Nat Biotechnol*. 2017;35(4):316-319. doi:10.1038/nbt.3820

Lamprecht AL, Garcia L, Kuzak M, et al. Towards interoperable and reproducible biomedical analyses: An Open Community's hacking of the nf-core framework. *F1000Res*. 2020;9:33. doi:10.12688/f1000research.20874.3

Simmonds P, Tusubo P, Leitner T. Unified nomenclature for theICTV virus taxonomy. *Nat Rev Microbiol*. 2019;17:131. doi:10.1038/s41579-018-0128-7

Zadeh AH, Houldcroft CJ, Lythgoe KA. Deep sequencing of viral genomes. *Viruses*. 2021;13(2):195. doi:10.3390/v13020195
