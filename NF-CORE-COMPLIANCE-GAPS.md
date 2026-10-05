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
- ✅ **Metro map diagram** - SVG and PNG showing complete pipeline workflow
  - All processing steps accurately represented
  - Color-coded paths for different workflow branches
  - Embedded in README for visibility

### Configuration Files  
- ✅ **conf/base.config** - Resource labels with retry/error strategy
  - process_single, process_low, process_medium, process_high, process_long, process_high_memory
  - Error strategy with retry logic
  - MaxRetries and maxErrors settings

- ✅ **conf/modules.config** - Module-specific configurations (copied from root)
- ✅ **conf/test.config** - Test profile with bundled data
- ✅ **conf/test_full.config** - Full test profile

### Nextflow Configuration
- ✅ **nf-schema plugin** (v2.2.0) for parameter validation
- ✅ **process.resourceLimits** for resource enforcement (Nextflow >=24.04)
- ✅ **CI resource caps** in test.config (4 CPUs, 15 GB memory, 6h time)
- ✅ **input parameter** (with samplesheet alias for backwards compatibility)
- ✅ **help, show_hidden, validate_params** parameters  
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

## 🚫 Intentionally Skipped

### Not Applicable to Research-Only Pipeline
- 🚫 **nf-core namespace** (`manifest.name` = 'sjoclaudi/nf-codonyat')
  - Reason: Independent pipeline, not part of nf-core organization
  - nf-core namespace reserved for official nf-core pipelines

- 🚫 **nf-core custom configs**
  - `params.custom_config_version`, `params.custom_config_base`
  - Reason: Not using nf-core institutional configs system
  - Alternative: Users can use `-c` flag for custom configs

- 🚫 **Email templates** (assets/email_template.txt, assets/sendmail_template.txt)
  - Reason: Research pipeline doesn't include email notifications
  - Impact: None - feature not needed for target use case

- 🚫 **nf-core logo files**  
  - assets/nf-core-nf-codonyat_logo_*.png in assets/ and docs/images/
  - Reason: Independent pipeline with own identity
  - Alternative: Can add sjoclaudi/nf-codonyat logos if desired

### Documentation Files (Lower Priority)
- 🚫 **docs/README.md** - Redundant with root README.md
- 🚫 **tests/default.nf.test** - Have tests/main.nf.test instead

### Advanced Features (Not Required)
- 🚫 **tower.yml** - Seqera Platform integration
  - Reason: Can be added by users who need it
  - Not required for core functionality

- 🚫 **RO-Crate / nf-prov** - Research Object packaging
  - Reason: Not a Nextflow 26 plugin, requires external workflow
  - Existing PROVENANCE process captures sufficient metadata for research use
  - See docs/NF-PROV-EVALUATION.md for full evaluation

- 🚫 **Pre-commit config** - Git hooks for code quality
  - Reason: Small team, can be added later
  - Standard .editorconfig and .prettierrc.yml provided

## 📊 Impact Assessment

### High Priority (Completed)
- ✅ Metro map visualization
- ✅ Resource configuration with retry strategy
- ✅ nf-schema validation
- ✅ Standard documentation files
- ✅ Test configurations

### Medium Priority (Partial / Future)
- ⚠️ Container configuration files (blocked by Nextflow config parsing)
- ⚠️ Updated nextflow_schema.json
- 🚫 Email notifications (explicitly not needed)

### Low Priority (Optional / Not Needed)
- 🚫 nf-core branding
- 🚫 Institutional configs
- 🚫 Advanced platform integrations

## Research Use Only Compliance

All changes maintain the research-use-only scope:
- No clinical interpretation
- No drug-resistance analysis  
- Clear disclaimers in documentation and MultiQC
- Descriptive outputs only (QC, contamination, subtype estimates, frequency tables)

## Next Steps (If Desired)

1. Fix check_max() function format to allow container config generation
2. Regenerate nextflow_schema.json with nf-core schema tool
3. Add testsDir to nf-test.config
4. Update tests/nextflow.config with testdata base paths
5. Consider adding pipeline logo
6. Consider Seqera Platform configuration (tower.yml) for Cloud deployment users
