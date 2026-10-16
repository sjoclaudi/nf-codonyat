# hiv1_subtype_panel_v1 — HIV-1 subtype estimation panel (A / B / M), pol region

Used by the subtype step (BBSplit competitive mapping; `--subtype_panel`). The
result is a **read-mapping based estimate for research use only**: the % of
reads that map best to each bin. It is not a genotyping result.

| Bin | Sequences | Source |
|---|---|---|
| **A** | A1 references DQ676872 (PS1044_Day0), AB253421 (92RW008), AB253429 (92UG037_A40) | LANL HIV Sequence Database, alignment type "Subtype reference", HIV-1/SIVcpz, POL, DNA, year 2026 (alignment ID 126RP8) |
| **B** | K03455 (HXB2), AY423387 (671_00T36), AY173951 (BK132), AY331295 (1058_11) | same alignment |
| **M** | `CON_OF_CONS`: group M consensus of the subtype consensus sequences (A, B, C, D, F, G, H weighted equally, CRFs excluded) | LANL "Consensus/Ancestral", HIV-1/SIVcpz, POL, DNA, year 2004 (alignment ID 104CP7) |

All sequences are the pol region (HXB2 2085–5096 equivalent, ~3 kb), gaps removed.
Rebuild with `bash build_panel.sh` (downloads from LANL) and check with
`sha256sum -c SHA256SUMS`.

## Interpretation (to confirm by Marc)

"M" is read as HIV-1 **group M** (which contains A, B, C, D, …). Its single
consensus sequence is roughly central — about equally distant from every
subtype — so in competitive mapping it acts as a **catch-all for group M
reads that are neither A nor B** (C, D, F, G, CRFs, …). Reports label this bin
"group M, not assigned to A or B". Because the consensus is central, some
divergent A or B reads can also land on M; the margin and the ambiguous-read
fraction in the report show this.

## Notes

- The proposal named the LANL **2005** A1 reference set (U51190, AF004885,
  AF069670, AF484509). LANL's maintained subtype reference set (2026) now uses
  the three A1 sequences above, so the current set is used. The B references are
  the same as proposed.
- LANL's 2021 consensus set has no group M consensus, so the 2004 `CON_OF_CONS`
  (the most recent LANL group M consensus) is used.
- GenBank sequences are public. Cite the LANL HIV Sequence Database
  (https://www.hiv.lanl.gov) when publishing; check LANL's reuse terms before
  redistributing the panel outside this pipeline **[verify]**.
