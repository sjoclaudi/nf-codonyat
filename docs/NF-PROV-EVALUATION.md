# nf-prov Plugin Evaluation for nf-codonyat

## Summary

**nf-prov is NOT added** to nf-codonyat at this time because:

1. **Nextflow 26.04.6 does not include nf-prov as a built-in plugin**
   - Running `nextflow help` and `nextflow -h` shows no prov or provenance flags
   - The plugin registry does not list nf-prov as an available plugin for Nextflow 26

2. **nf-prov is a separate workflow/tool, not a Nextflow plugin**
   - nf-prov is implemented as a standalone workflow that post-processes Nextflow outputs
   - It requires additional setup and is not integrated into the core Nextflow execution engine

3. **Provenance is already captured via existing mechanisms**
   - nf-codonyat already includes a `PROVENANCE` process that captures:
     - Pipeline version and parameters
     - Software versions (codonyat, fastp, bowtie2, etc.)
     - Input metadata and execution timestamps
   - MultiQC aggregates provenance information from all tools
   - `.nextflow.log` and execution reports provide full audit trails

4. **Research use disclaimer**
   - nf-codonyat is explicitly for research use only
   - Clinical-grade provenance (e.g., RO-Crate bundles) would be required for diagnostic use
   - Current provenance mechanisms are appropriate for research workflows

## Future Consideration

If nf-prov becomes available as a Nextflow plugin in future releases, or if nf-codonyat transitions to clinical/diagnostic use, we can:

1. Add nf-prov as a plugin in `nextflow.config`:
   ```groovy
   plugins {
       id 'nf-schema@2.2.0'
       id 'nf-prov@x.y.z'  // When available
   }
   ```

2. Configure RO-Crate output for W3C PROV-compliant provenance bundles

3. Integrate with research data repositories that require FAIR provenance metadata

## References

- Nextflow documentation: https://www.nextflow.io/docs/latest/
- nf-prov repository: https://github.com/iwc-workflows/nf-prov
- W3C PROV: https://www.w3.org/TR/prov-overview/
