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
PROTEIN_HEADER_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)\(([^)]*)\):([0-9,-]+)")


def translate(codon: str) -> str:
    codon = codon.upper()
    if codon == "---":
        return "del"
    return CODE.get(codon, "X")


def parse_intervals(text: str) -> list[tuple[int, int]]:
    sep = ";" if ";" in text else ","
    out = []
    for part in text.split(sep):
        part = part.strip()
        if not part:
            continue
        a, b = part.split("-", 1)
        out.append((int(a), int(b)))
    return out


def read_reference(path: str) -> tuple[dict[str, str], dict[tuple[str, str], list[tuple[int, int]]]]:
    """Return {record: seq} and {(record, protein): [(start, end), ...]} (1-based inclusive)."""
    seqs: dict[str, str] = {}
    proteins: dict[tuple[str, str], list[tuple[int, int]]] = {}
    rid, chunks = None, []
    with open(path) as fh:
        for line in fh:
            if line.startswith(">"):
                if rid is not None:
                    seqs[rid] = "".join(chunks).upper()
                header = line[1:].strip()
                rid = header.split()[0]
                chunks = []
                for m in PROTEIN_HEADER_RE.finditer(header):
                    proteins[(rid, m.group(1))] = parse_intervals(m.group(3))
            else:
                chunks.append(line.strip())
        if rid is not None:
            seqs[rid] = "".join(chunks).upper()
    return seqs, proteins


def aa_index_and_codon(seq: str, intervals: list[tuple[int, int]], nt_pos: int) -> tuple[str, str]:
    """Codon index (1-based along joined CDS) and reference codon at a genomic nt_pos."""
    joined = []
    genomic = []
    for start, end in intervals:
        for g in range(start, end + 1):
            joined.append(seq[g - 1] if 0 <= g - 1 < len(seq) else "N")
            genomic.append(g)
    if nt_pos not in genomic:
        start = intervals[0][0] if intervals else None
        aa_pos = (nt_pos - start) // 3 + 1 if start else ""
        codon = seq[nt_pos - 1 : nt_pos + 2]
        return aa_pos, codon
    i = genomic.index(nt_pos)
    codon_i = i // 3
    codon = "".join(joined[codon_i * 3 : codon_i * 3 + 3])
    return codon_i + 1, codon


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

    seqs, proteins = read_reference(args.reference)
    default_rid = next(iter(seqs), "")
    multi = len(seqs) > 1
    strand = read_strand(args.strand)
    groups: "OrderedDict[tuple, dict]" = OrderedDict()
    with open(args.codons) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            protein, pos = r["PROTEIN"], int(r["POSITION"])
            rid = r.get("RECORD") or r.get("REFERENCE") or default_rid
            aa = translate(r["VARIANT"])
            key = (rid, protein, pos, aa)
            g = groups.get(key)
            if g is None:
                g = groups[key] = {"freq": 0.0, "codons": [], "row": r, "rid": rid}
            g["freq"] += float(r["FREQ"])
            g["codons"].append(f"{r['VARIANT']}:{r['FREQ']}")

    out = sys.stdout
    columns = COLUMNS + (["RECORD"] if multi else []) + (STRAND_COLUMNS if args.strand else [])
    out.write("\t".join(columns) + "\n")
    for (rid, protein, pos, aa), g in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], -kv[1]["freq"], kv[0][3])):
        r = g["row"]
        iv = proteins.get((rid, protein)) or proteins.get((default_rid, protein), [])
        seq = seqs.get(rid) or seqs.get(default_rid, "")
        if iv:
            aa_pos, ref_codon = aa_index_and_codon(seq, iv, pos)
        else:
            aa_pos, ref_codon = "", seq[pos - 1 : pos + 2]
        values = {
            "SAMPLE": args.sample, "PROTEIN": protein, "AA_POSITION": aa_pos, "NT_POSITION": pos,
            "REF_CODON": ref_codon, "REF_AA": translate(ref_codon), "AA": aa,
            "FREQ": round(g["freq"], 3), "CODONS": ",".join(g["codons"]),
            "TOTALCOV": r["TOTALCOV"], "FWCOV": r["FWCOV"], "RVCOV": r["RVCOV"], "RATIO": r["RATIO"],
            "RECORD": rid,
        }
        if args.strand:
            s = strand.get((protein, pos), {})
            values.update({c: s.get(c, "NA") for c in STRAND_COLUMNS})
        out.write("\t".join(str(values[c]) for c in columns) + "\n")


if __name__ == "__main__":
    main()
