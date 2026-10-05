#!/usr/bin/env python3
"""Tidy an iVar consensus and report indels and coverage statistics.

    consensus_report.py --sample S --fasta S.fa --mpileup S.mpileup --reference-id K03455 \
        --threshold 0.5 --min-depth 100 [--report-min-freq 0.05]

Writes:
  S.consensus.fa          consensus with header ">S|<reference>|t<threshold>_m<min depth>"
  S.consensus_indels.tsv  indels seen in the pileup at >= --report-min-freq of depth:
                          POSITION (reference coordinate: first deleted base for deletions,
                          the base after which an insertion sits for insertions), TYPE, LENGTH,
                          SEQUENCE, COUNT, DEPTH, FREQ, APPLIED (expected in the consensus: freq >=
                          threshold, or >= insertion threshold for insertions, and depth >= min depth),
                          FRAMESHIFT (length % 3 != 0, per event)
  S.consensus_stats.tsv   consensus length, N count, IUPAC-ambiguity count, positions at >= min depth

Research use only.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter

INDEL_RE = re.compile(r"([+-])(\d+)")
AMBIG = set("RYSWKMBDHV")


def parse_bases(bases: str) -> Counter:
    """Count indel events ('+ACG' / '-AC') in an mpileup bases column."""
    events: Counter = Counter()
    i, n = 0, len(bases)
    while i < n:
        c = bases[i]
        if c == "^":
            i += 2
            continue
        if c in "+-":
            m = INDEL_RE.match(bases, i)
            length = int(m.group(2))
            start = m.end()
            seq = bases[start : start + length].upper()
            events[("insertion" if c == "+" else "deletion", length, seq)] += 1
            i = start + length
            continue
        i += 1
    return events


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", required=True)
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--mpileup", required=True)
    ap.add_argument("--reference-id", required=True)
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--insertion-threshold", type=float, default=None,
                    help="iVar -c (default: same as --threshold)")
    ap.add_argument("--min-depth", type=int, required=True)
    ap.add_argument("--report-min-freq", type=float, default=0.05)
    args = ap.parse_args(argv)
    if args.insertion_threshold is None:
        args.insertion_threshold = args.threshold

    seq = "".join(line.strip() for line in open(args.fasta) if not line.startswith(">"))
    tag = f"t{args.threshold:g}_m{args.min_depth}"
    with open(f"{args.sample}.consensus.fa", "w") as fh:
        fh.write(f">{args.sample}|{args.reference_id}|{tag}\n")
        for i in range(0, len(seq), 70):
            fh.write(seq[i : i + 70] + "\n")

    covered = 0
    with open(args.mpileup) as fh, open(f"{args.sample}.consensus_indels.tsv", "w") as out:
        out.write("SAMPLE\tPOSITION\tTYPE\tLENGTH\tSEQUENCE\tCOUNT\tDEPTH\tFREQ\tAPPLIED\tFRAMESHIFT\n")
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            pos, depth = int(parts[1]), int(parts[3])
            if depth >= args.min_depth:
                covered += 1
            if depth == 0 or ("+" not in parts[4] and "-" not in parts[4]):
                continue
            for (kind, length, iseq), count in sorted(parse_bases(parts[4]).items()):
                freq = count / depth
                if freq < args.report_min_freq:
                    continue
                cutoff = args.insertion_threshold if kind == "insertion" else args.threshold
                applied = freq >= cutoff and depth >= args.min_depth
                # deletions: first deleted reference base; insertions: base after which the insertion sits
                where = pos + 1 if kind == "deletion" else pos
                out.write(f"{args.sample}\t{where}\t{kind}\t{length}\t{iseq}\t{count}\t{depth}\t{freq:.4f}\t"
                          f"{'yes' if applied else 'no'}\t{'yes' if length % 3 else 'no'}\n")

    n_count = seq.upper().count("N")
    ambiguous = sum(1 for c in seq.upper() if c in AMBIG)
    with open(f"{args.sample}.consensus_stats.tsv", "w") as fh:
        fh.write("SAMPLE\tCONSENSUS_LENGTH\tN_COUNT\tPCT_N\tIUPAC_AMBIGUOUS\tPOSITIONS_AT_MIN_DEPTH\tTHRESHOLD\tMIN_DEPTH\n")
        pct_n = round(100.0 * n_count / len(seq), 2) if seq else 0.0
        fh.write(f"{args.sample}\t{len(seq)}\t{n_count}\t{pct_n}\t{ambiguous}\t{covered}\t{args.threshold:g}\t{args.min_depth}\n")


if __name__ == "__main__":
    main()
