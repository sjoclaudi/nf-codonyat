#!/usr/bin/env bash
# Rebuild hiv1_subtype_panel_v1 (A / B / M bins, HIV-1 pol region) from the
# LANL HIV Sequence Database alignments. Run from this directory:
#   bash build_panel.sh && sha256sum -c SHA256SUMS
#
#   A, B : LANL "Subtype reference" alignment, HIV-1/SIVcpz, POL, DNA, 2026
#          (alignment ID 126RP8): all A1 and B reference sequences.
#   M    : LANL "Consensus/Ancestral" alignment, HIV-1/SIVcpz, POL, DNA, 2004
#          (alignment ID 104CP7): CON_OF_CONS, the group M consensus of the
#          subtype consensuses (A, B, C, D, F, G, H weighted equally, CRFs excluded).
# Gaps are removed and bases upper-cased. Requires curl and python3.
set -euo pipefail
LANL=https://www.hiv.lanl.gov
fetch() {  # $1=ALIGN_TYPE $2=YEAR $3=output
    local page url
    page=$(curl -fsSL -F ALIGN_TYPE="$1" -F ORGANISM=HIV -F SUBORGANISM=HIV1 -F PRE_USER=predefined \
        -F REGION=POL -F GENO_SUB=All -F BASETYPE=DNA -F YEAR="$2" -F FORMAT=fasta \
        -F submit="Get Alignment" "$LANL/cgi-bin/NEWALIGN/align.cgi")
    url=$(grep -o 'download.cgi?[^"]*fasta' <<<"$page" | head -1)
    curl -fsSL "$LANL/cgi-bin/common_code/$url" -o "$3"
}
tmp=$(mktemp -d)
fetch REF 2026 "$tmp/ref.fasta"
fetch CON 2004 "$tmp/con.fasta"
python3 - "$tmp/ref.fasta" "$tmp/con.fasta" <<'PY'
import sys
def read(path):
    seqs, name = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"):
            name = line[1:]; seqs[name] = []
        elif name:
            seqs[name].append(line)
    return {k: "".join(v).replace("-", "").replace(".", "").upper() for k, v in seqs.items()}
ref, con = read(sys.argv[1]), read(sys.argv[2])
bins = {
    "A": [k for k in ref if k.startswith("Ref.A1.")],
    "B": [k for k in ref if k.startswith("Ref.B.")],
}
rows = []
for b, names in bins.items():
    with open(f"{b}.fa", "w") as fh:
        for n in names:
            fh.write(f">{n}\n{ref[n]}\n")
            rows.append((b, n, n.rsplit(".", 1)[1], len(ref[n]), "LANL subtype reference 2026 (126RP8), pol"))
with open("M.fa", "w") as fh:
    fh.write(f">CON_OF_CONS.group_M_consensus\n{con['CON_OF_CONS']}\n")
rows.append(("M", "CON_OF_CONS.group_M_consensus", "none (LANL consensus)", len(con["CON_OF_CONS"]),
             "LANL consensus/ancestral 2004 (104CP7), pol"))
with open("panel.tsv", "w") as fh:
    fh.write("bin\tsequence\taccession\tlength\tsource\n")
    for r in rows:
        fh.write("\t".join(map(str, r)) + "\n")
PY
sha256sum A.fa B.fa M.fa panel.tsv > SHA256SUMS
rm -rf "$tmp"
