# nf-codonyat v0.5.0 Implementation Summary

**Branch:** cursor/feat-v0.5.0-e211  
**Status:** Partial implementation - core framework complete, some features pending

## Completed

### Core Infrastructure
- ✅ Version bumped to 0.5.0 in `nextflow.config`
- ✅ Updated to codonyat==1.2.0 in `environment.yml`
- ✅ Updated nextflow_schema.json with all new parameters
- ✅ Created preset system framework
- ✅ HIV-1 preset structure created in `assets/presets/hiv1/`
  - Reference, amplicons, subtype_panel moved into preset
  - preset.yml with target_taxid=11676, target_label=HIV1
- ✅ Generic contamination tracking implemented
  - Updated `bin/contamination_summary.py` with TARGET_TAXID, TARGET_READS, TARGET_PCT columns
  - HIV1_* columns preserved for backward compatibility
  - Support for deprecated `contamination_warn_hiv_pct` parameter
- ✅ Updated `main.nf` with preset loading logic
- ✅ Updated `workflows/codonyat.nf` to accept target_taxid, target_label, subtype_panel
- ✅ Updated contamination summary module to use generic parameters
- ✅ Test configuration updated to use hiv1 preset
- ✅ Comprehensive CHANGELOG.md for v0.5.0
- ✅ Updated documentation (usage.md, output.md)
- ✅ Updated README.md

### Validation
- ✅ Validation script created (`bin/validate_reference.py`)
  - Reference size limit check (100kb for custom)
  - Primer BED validation (pairing, coordinates, naming)
  - Annotation validation (CDS bounds, length, strand)
  - Amplicon/CDS overlap check
  - Machine-readable validation.json output

### Helper Scripts
- ✅ Preset loader created (`bin/load_preset.py`)
  - Loads preset.yml configuration
  - Resolves paths for reference, amplicons, primers, subtype_panel
  - Returns JSON with target_taxid and target_label

## Partially Implemented / TODO

### Features Marked as TODO in Code
1. **Primer BED to amplicons conversion**: Not yet implemented
   - Currently requires presets to have amplicons.tsv
   - Error thrown if user provides --primer-bed without --amplicons
   - Would need a module to convert 6-column BED to 7-column amplicon TSV

2. **validate_only mode**: Framework only
   - Parameter defined and validated
   - Stub implementation that exits with error
   - Would need a proper Nextflow module wrapping validate_reference.py

3. **New output modules**: Not created
   - `reference/annotation_used.tsv`
   - `reference/amplicons_used.tsv`
   - `reference/reference_used.fasta`
   - `pipeline_info/run_mode.json`
   - These would need new publishing modules

### Additional Presets
Only HIV-1 preset fully created. Other presets need:
- SARS-CoV-2: Reference (MN908947.3), ARTIC primer scheme (BED), GFF3 annotation
- Influenza A: Multi-record reference (8 segments), primers (unverified), annotation
- RSV, HBV, HCV: References, primers (unverified), annotations

**Note**: Design doc section 9 states primer schemes for non-HIV presets should be marked as "unverified" until validated.

### Testing
- ❌ SARS-CoV-2 test profile not created
- ❌ No test data for multi-record references
- ❌ HIV-1 backward compatibility test not run (requires Docker execution)

### Container
- ⚠️ Container still references 0.3.0 in modules
  - Would need new container build with codonyat 1.2.0
  - Currently: `ghcr.io/sjoclaudi/nf-codonyat:0.3.0`
  - Need: `ghcr.io/sjoclaudi/nf-codonyat:0.5.0`

## Deviations from Requirements

1. **Branch name**: Created `cursor/feat-v0.5.0-e211` instead of `feat/v0.5.0` per naming template
2. **Pull Request**: Could not create due to permission error ("must be a collaborator")
3. **Primer BED support**: Marked as TODO - not fully implemented
4. **validate_only**: Marked as TODO - not fully implemented
5. **Additional presets**: Only HIV-1 created; others require validated primer schemes
6. **Output files**: New output modules (reference/, run_mode.json) not created

## Git Activity Summary

### Commits (7 total)
1. `54a47bf` - feat: add v0.5.0 base parameters and hiv1 preset structure
2. `039d23f` - feat: add reference validation script
3. `dd0033e` - feat: update schema for v0.5.0 parameters
4. `39562e4` - feat: implement preset loading and parameter resolution
5. `bc83f28` - feat: update to codonyat 1.2.0 and add CHANGELOG for v0.5.0
6. `dcb71a6` - docs: update usage and output documentation for v0.5.0
7. `7e8f149` - fix: correct preset resolution and validation mode stubs

### Pushes
- All commits pushed to `origin/cursor/feat-v0.5.0-e211`
- Branch created and pushed early per requirements
- Frequent commits and pushes as instructed

## Backward Compatibility

✅ **HIV-1 outputs should remain identical to v0.4.0** except:
- Appended TARGET_TAXID, TARGET_READS, TARGET_PCT columns in contamination tables
- New files in reference/ and pipeline_info/
- Updated provenance metadata

The test profile has been updated but not executed to verify this claim.

## Next Steps for Completion

1. Implement primer BED to amplicons TSV converter
2. Create validate_only Nextflow module
3. Create output modules for new files (reference/, run_mode.json)
4. Build and publish new container with codonyat 1.2.0
5. Create additional virus presets with verified primer schemes
6. Add SARS-CoV-2 test profile with test data
7. Run full backward compatibility test (HIV-1 v0.4.0 vs v0.5.0)
8. Update Dockerfile to codonyat 1.2.0

## Risk Assessment

**High Priority:**
- Container update required before pipeline will run
- Primer BED functionality advertised but not working

**Medium Priority:**
- Additional presets needed for multi-virus support
- Test coverage incomplete

**Low Priority:**
- validate_only is a convenience feature
- New output files are supplementary

## Research Use Only

All work maintains the "research use only" disclaimer throughout. No clinical, diagnostic, or resistance interpretation features have been added.
