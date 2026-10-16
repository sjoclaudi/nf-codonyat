#!/usr/bin/env python3
"""Tidy an iVar consensus and report indels and coverage statistics.

    consensus_report.py --sample S --fasta S.fa --mpileup S.mpileup --reference-id K03455 \
        --threshold 0.5 --min-depth 100 [--report-min-freq 0.05]

Writes:
  S.consensus.fa          consensus with header ">S|<reference>|t<threshold>_m<min depth>"
                          (one record per reference contig when iVar was run per record)
  S.consensus_indels.tsv  indels seen in the pileup at >= --report-min-freq of depth
  S.consensus_stats.tsv   consensus length, N count, IUPAC-ambiguity count, positions at >= min depth

Single-record outputs keep the v0.4.0 columns and FASTA header shape.
Research use only.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter

INDEL_RE = re.compile(r"([+-])(\d+)")
AMBIG = set("RYSWKMBDHV")


def parse_fasta(path: str) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    name, seq = None, []
    with open(path) as fh:
        for line in fh:
            if line.startswith(">"):
                if name is not None:
                    records.append((name, "".join(seq)))
                name = line[1:].strip().split()[0]
                seq = []
            else:
                seq.append(line.strip())
        if name is not None:
            records.append((name, "".join(seq)))
    return records


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


def write_fasta(path: str, records: list[tuple[str, str]]) -> None:
    with open(path, "w") as fh:
        for name, seq in records:
            fh.write(f">{name}\n")
            for i in range(0, len(seq), 70):
                fh.write(seq[i : i + 70] + "\n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", required=True)
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--mpileup", required=True)
    ap.add_argument("--reference-id", required=True, help="First FASTA id, or comma-separated ids")
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--insertion-threshold", type=float, default=None,
                    help="iVar -c (default: same as --threshold)")
    ap.add_argument("--min-depth", type=int, required=True)
    ap.add_argument("--report-min-freq", type=float, default=0.05)
    args = ap.parse_args(argv)
    if args.insertion_threshold is None:
        args.insertion_threshold = args.threshold

    ivar_records = parse_fasta(args.fasta)
    if not ivar_records:
        ivar_records = [("", "")]
    ref_ids = [r for r in args.reference_id.split(",") if r]
    tag = f"t{args.threshold:g}_m{args.min_depth}"
    multi = len(ivar_records) > 1 or len(ref_ids) > 1

    cons_records = []
    for i, (raw_name, seq) in enumerate(ivar_records):
        rid = ref_ids[i] if i < len(ref_ids) else (ref_ids[0] if ref_ids else raw_name)
        cons_records.append((f"{args.sample}|{rid}|{tag}", seq))
    write_fasta(f"{args.sample}.consensus.fa", cons_records)

    # Per-contig covered-base counts (mpileup column 1 = contig)
    covered_by_contig: dict[str, int] = Counter()
    covered = 0
    indel_header = "SAMPLE\tPOSITION\tTYPE\tLENGTH\tSEQUENCE\tCOUNT\tDEPTH\tFREQ\tAPPLIED\tFRAMESHIFT"
    if multi:
        indel_header += "\tRECORD"
    with open(args.mpileup) as fh, open(f"{args.sample}.consensus_indels.tsv", "w") as out:
        out.write(indel_header + "\n")
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            contig, pos, depth = parts[0], int(parts[1]), int(parts[3])
            if depth >= args.min_depth:
                covered += 1
                covered_by_contig[contig] += 1
            if depth == 0 or ("+" not in parts[4] and "-" not in parts[4]):
                continue
            for (kind, length, iseq), count in sorted(parse_bases(parts[4]).items()):
                freq = count / depth
                if freq < args.report_min_freq:
                    continue
                cutoff = args.insertion_threshold if kind == "insertion" else args.threshold
                applied = freq >= cutoff and depth >= args.min_depth
                where = pos + 1 if kind == "deletion" else pos
                row = (
                    f"{args.sample}\t{where}\t{kind}\t{length}\t{iseq}\t{count}\t{depth}\t{freq:.4f}\t"
                    f"{'yes' if applied else 'no'}\t{'yes' if length % 3 else 'no'}"
                )
                if multi:
                    row += f"\t{contig}"
                out.write(row + "\n")

    stats_header = "SAMPLE\tCONSENSUS_LENGTH\tN_COUNT\tPCT_N\tIUPAC_AMBIGUOUS\tPOSITIONS_AT_MIN_DEPTH\tTHRESHOLD\tMIN_DEPTH"
    if multi:
        stats_header += "\tRECORD"
    with open(f"{args.sample}.consensus_stats.tsv", "w") as fh:
        fh.write(stats_header + "\n")
        if multi:
            for header, seq in cons_records:
                rid = header.split("|")[1] if "|" in header else header
                n_count = seq.upper().count("N")
                ambiguous = sum(1 for c in seq.upper() if c in AMBIG)
                pct_n = round(100.0 * n_count / len(seq), 2) if seq else 0.0
                cov = covered_by_contig.get(rid, 0)
                fh.write(
                    f"{args.sample}\t{len(seq)}\t{n_count}\t{pct_n}\t{ambiguous}\t{cov}\t"
                    f"{args.threshold:g}\t{args.min_depth}\t{rid}\n"
                )
        else:
            seq = cons_records[0][1]
            n_count = seq.upper().count("N")
            ambiguous = sum(1 for c in seq.upper() if c in AMBIG)
            pct_n = round(100.0 * n_count / len(seq), 2) if seq else 0.0
            fh.write(
                f"{args.sample}\t{len(seq)}\t{n_count}\t{pct_n}\t{ambiguous}\t{covered}\t"
                f"{args.threshold:g}\t{args.min_depth}\n"
            )


if __name__ == "__main__":
    main()
