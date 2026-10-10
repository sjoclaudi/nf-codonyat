# nf-core Compliance Gap Analysis

## Summary

Based on nf-core lint checks and nf-core/tools best practices.

**Initial State (baseline):**
- Passed: 119 tests
- Warned: 13 tests  
- Failed: 56 tests
- Ignored: 21 tests

## ✅ Implemented (Completed)

### Visual Documentation
- ✅ **Metro map diagram** - hand-laid SVG + PNG (2x) regenerated from the real workflow
  - Sections: input, pre-processing/QC, contamination (Kraken2), subtyping (BBSplit),
    merge+alignment, strand branch, consensus (iVar), codon/AA tables, reporting
  - Horizontal / vertical / 45° segments only; labels beside stations; legend; research-use footer
  - Generator: `docs/images/make_metro_map.py`; copy also at `/workspace/nf-codonyat-metro-map.png`

### Configuration Files  
- ✅ **conf/base.config** - Resource labels with retry/error strategy
  - process_single, process_low, process_medium, process_high, process_long, process_high_memory
  - Error strategy with retry logic
  - MaxRetries and maxErrors settings

- ✅ **conf/modules.config** - Module-specific configurations (copied from root)
- ✅ **conf/test.config** - Test profile with bundled data
- ✅ **conf/test_full.config** - Full test profile

### Nextflow Configuration
- ✅ **nf-schema plugin** (v2.8.0) for parameter validation and `--help`
- ✅ **process.resourceLimits** for resource enforcement (Nextflow >=24.04)
- ✅ **CI resource caps** in test.config (4 CPUs, 15 GB memory, 6h time)
- ✅ **input parameter** (with samplesheet alias for backwards compatibility)
- ✅ **help, helpFull, showHidden, validate_params** parameters  
- ✅ **podman profile** added
- ✅ **Proper includeConfig** structure (conf/base.config, conf/test.config)
- ✅ **Manifest updates**: author, doi field placeholder

### Validation and Schema
- ✅ **assets/schema_input.json** - Samplesheet validation schema
- ✅ **assets/multiqc_config.yml** - MultiQC configuration with research-use-only disclaimer

### Documentation
- ✅ **CITATIONS.md** - Comprehensive tool citations
- ✅ **CODE_OF_CONDUCT.md** - Contributor Covenant 2.0
- ✅ **docs/CONTRIBUTING.md** - Contribution guidelines
- ✅ **.editorconfig** - Editor configuration
- ✅ **.prettierrc.yml** - Code style configuration
- ✅ **LICENSE** - Fixed merge conflict markers

### Testing
- ✅ Outputs remain byte-identical to v0.3.1 baseline (see docs/BYTE-IDENTICAL-VERIFICATION.md)
- ✅ Test profile runs successfully with both docker and conda
- ✅ nf-test suite passes (2 main tests)
- ✅ CI tests green on GitHub Actions (run 37268979895)

## ⚠️ Partially Implemented / Needs Work

### Container Configurations
- ✅ **Container configs resolved** by moving to process.resourceLimits
  - Removed check_max() function that caused parsing failures
  - Modern Nextflow >=24.04 approach with resourceLimits
  - All profiles (docker, singularity, podman, conda) work correctly

### nf-test Configuration  
- ⚠️ **tests/nextflow.config missing testdata paths**
  - Missing: modules_testdata_base_path, pipelines_testdata_base_path
  - Impact: Low - tests run successfully without these

- ⚠️ **nf-test.config missing testsDir**
  - Should contain: `testsDir = "."`
  - Impact: Low - tests work with current setup

### Schema Updates
- ✅ **nextflow_schema.json regenerated**
  - Regenerated with nf-core schema build (37 parameters)
  - Includes: input parameter, all process parameters, help, validate_params
  - Enables --help output and full validation

## ✅ nf-prov (added)

- Official Nextflow plugin `nf-prov@1.7.0` (BCO / WRROC / DAG)
- Disabled by default; enable with `--prov_enabled true`
- Reports written under `<outdir>/pipeline_info/` (`bco.json`, `ro-crate-metadata.json`, `prov_dag.html`)
- Existing local `PROVENANCE` process (methods.md, software_versions.yml, provenance.json) kept
- Deleted the incorrect `docs/NF-PROV-EVALUATION.md` (it wrongly claimed nf-prov is not a Nextflow plugin)

## 🚫 Intentionally skipped

- **nf-core namespace** — independent research pipeline; still follows nf-core practices
- **nf-core custom configs** — not needed
- **Email templates** — not required for this research pipeline

## 🔬 Research use only

- No clinical / diagnostic interpretation; no drug-resistance analysis
- Short disclaimers in docs, MultiQC, provenance, and the metro-map footer
- No speculation about future clinical use
