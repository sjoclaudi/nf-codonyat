#!/usr/bin/env python3
"""Amino-acid frequency table from a codonyat codon table (frequencies only, no interpretation).

    codon_to_aa.py --sample S --codons S.tsv --reference reference.fasta \
        [--strand S.strand_metrics_unmerged.tsv] > S.aa_variants.tsv

One row per (protein, codon position, amino acid): codon frequencies that
translate to the same amino acid are summed. Codons with a gap in all three
bases are reported as "del"; codons with a partial gap or a non-ACGT base as "X";
stops as "*". When a strand-metrics table from the unmerged-read alignment is
given, FWCOV/RVCOV/RATIO from that alignment are added as *_UNMERGED columns.
Research use only: no drug, resistance or clinical annotation.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import OrderedDict

BASES = "TCAG"
AMINO = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
CODE = {a + b + c: AMINO[16 * i + 4 * j + k] for i, a in enumerate(BASES) for j, b in enumerate(BASES) for k, c in enumerate(BASES)}

COLUMNS = ["SAMPLE", "PROTEIN", "AA_POSITION", "NT_POSITION", "REF_CODON", "REF_AA", "AA", "FREQ", "CODONS",
           "TOTALCOV", "FWCOV", "RVCOV", "RATIO"]
STRAND_COLUMNS = ["FWCOV_UNMERGED", "RVCOV_UNMERGED", "TOTALCOV_UNMERGED", "RATIO_UNMERGED"]


def translate(codon: str) -> str:
    codon = codon.upper()
    if codon == "---":
        return "del"
    return CODE.get(codon, "X")


def read_reference(path: str) -> tuple[str, dict[str, int]]:
    header, seq = "", []
    with open(path) as fh:
        for line in fh:
            if line.startswith(">"):
                if header:
                    break
                header = line[1:].strip()
            else:
                seq.append(line.strip().upper())
    starts = {m.group(1): int(m.group(2)) for m in re.finditer(r"(\w+)\([^)]*\):(\d+)-\d+", header)}
    return "".join(seq), starts


def read_strand(path: str | None) -> dict[tuple[str, int], dict]:
    if not path:
        return {}
    with open(path) as fh:
        return {(r["PROTEIN"], int(r["POSITION"])): r for r in csv.DictReader(fh, delimiter="\t")}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", required=True)
    ap.add_argument("--codons", required=True, help="codonyat TSV (one or more proteins)")
    ap.add_argument("--reference", required=True, help="annotated reference FASTA")
    ap.add_argument("--strand", help="strand_metrics_unmerged TSV (optional)")
    args = ap.parse_args(argv)

    ref_seq, starts = read_reference(args.reference)
    strand = read_strand(args.strand)
    groups: "OrderedDict[tuple, dict]" = OrderedDict()
    with open(args.codons) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            protein, pos = r["PROTEIN"], int(r["POSITION"])
            aa = translate(r["VARIANT"])
            key = (protein, pos, aa)
            g = groups.get(key)
            if g is None:
                g = groups[key] = {"freq": 0.0, "codons": [], "row": r}
            g["freq"] += float(r["FREQ"])
            g["codons"].append(f"{r['VARIANT']}:{r['FREQ']}")

    out = sys.stdout
    columns = COLUMNS + (STRAND_COLUMNS if args.strand else [])
    out.write("\t".join(columns) + "\n")
    for (protein, pos, aa), g in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1]["freq"], kv[0][2])):
        r = g["row"]
        start = starts.get(protein)
        aa_pos = (pos - start) // 3 + 1 if start else ""
        ref_codon = ref_seq[pos - 1 : pos + 2]
        values = {
            "SAMPLE": args.sample, "PROTEIN": protein, "AA_POSITION": aa_pos, "NT_POSITION": pos,
            "REF_CODON": ref_codon, "REF_AA": translate(ref_codon), "AA": aa,
            "FREQ": round(g["freq"], 3), "CODONS": ",".join(g["codons"]),
            "TOTALCOV": r["TOTALCOV"], "FWCOV": r["FWCOV"], "RVCOV": r["RVCOV"], "RATIO": r["RATIO"],
        }
        if args.strand:
            s = strand.get((protein, pos), {})
            values.update({c: s.get(c, "NA") for c in STRAND_COLUMNS})
        out.write("\t".join(str(values[c]) for c in columns) + "\n")


if __name__ == "__main__":
    main()
