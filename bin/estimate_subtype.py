#!/usr/bin/env python3
"""HIV-1 subtype estimate from BBSplit refstats: % of reads mapped to each panel bin.

Per sample:
    estimate_subtype.py sample --sample S --stats S.stats.txt --primary-name A \
        --min-reads 100 --min-margin 10 > S.subtype.tsv
Combine:
    estimate_subtype.py combine S1.subtype.tsv ... --out subtype_summary.tsv --mqc subtype_mqc.tsv

Percentages use reads assigned unambiguously to one bin (BBSplit ambiguous2=toss).
Reads that tie between references of the same bin stay in that bin; reads that tie
between bins are reported as ambiguous. The M bin (group M consensus) is labelled
"group M, not assigned to A or B". Read-mapping based estimate for research use only;
not a genotyping result. Recombinants and other subtypes may split between bins.
"""

from __future__ import annotations

import argparse
import sys

LABELS = {"M": "group M, not assigned to A or B"}
COLUMNS = [
    "SAMPLE", "BIN", "LABEL", "READS", "PCT_OF_ASSIGNED", "AMBIGUOUS_READS",
    "CALL", "RUNNER_UP", "MARGIN_PCT_POINTS", "ASSIGNED_READS", "AMBIGUOUS_FRACTION", "FLAG",
]


def read_stats(path: str, primary_name: str) -> list[dict]:
    rows = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            name = primary_name if p[0] == "primary" else p[0]
            rows.append({"bin": name, "unambiguous": int(p[5]), "ambiguous": int(p[6])})
    return rows


def sample_rows(sample: str, stats: str, primary_name: str, bins: list[str], min_reads: int, min_margin: float) -> list[dict]:
    found = {r["bin"]: r for r in read_stats(stats, primary_name)}
    for b in bins:
        found.setdefault(b, {"bin": b, "unambiguous": 0, "ambiguous": 0})
    order = bins + sorted(b for b in found if b not in bins)
    assigned = sum(found[b]["unambiguous"] for b in order)
    max_ambiguous = max((found[b]["ambiguous"] for b in order), default=0)
    pcts = {b: (100.0 * found[b]["unambiguous"] / assigned if assigned else 0.0) for b in order}
    ranked = sorted(order, key=lambda b: (-pcts[b], order.index(b)))
    top, runner = ranked[0], (ranked[1] if len(ranked) > 1 else "")
    margin = pcts[top] - (pcts[runner] if runner else 0.0)
    if assigned < min_reads:
        call, flag = "undetermined", f"fewer_than_{min_reads}_assigned_reads"
    elif margin < min_margin:
        call, flag = top, "ambiguous_or_possible_recombinant"
    else:
        call, flag = top, "none"
    ambiguous_fraction = max_ambiguous / (assigned + max_ambiguous) if (assigned + max_ambiguous) else 0.0
    rows = []
    for b in order:
        rows.append({
            "SAMPLE": sample, "BIN": b, "LABEL": LABELS.get(b, f"subtype {b}"),
            "READS": found[b]["unambiguous"], "PCT_OF_ASSIGNED": round(pcts[b], 3),
            "AMBIGUOUS_READS": found[b]["ambiguous"],
            "CALL": call, "RUNNER_UP": runner, "MARGIN_PCT_POINTS": round(margin, 3),
            "ASSIGNED_READS": assigned, "AMBIGUOUS_FRACTION": round(ambiguous_fraction, 4), "FLAG": flag,
        })
    return rows


def write(rows: list[dict], out) -> None:
    out.write("# Estimated HIV-1 subtype (read-mapping based; research use only). Not a genotyping result.\n")
    out.write("\t".join(COLUMNS) + "\n")
    for r in rows:
        out.write("\t".join(str(r[c]) for c in COLUMNS) + "\n")


def read_tables(paths: list[str]) -> list[dict]:
    rows = []
    for path in paths:
        with open(path) as fh:
            lines = [ln for ln in fh if not ln.startswith("#") and ln.strip()]
        header = lines[0].rstrip("\n").split("\t")
        rows.extend(dict(zip(header, ln.rstrip("\n").split("\t"))) for ln in lines[1:])
    return sorted(rows, key=lambda r: r["SAMPLE"])


def write_mqc(rows: list[dict], path: str) -> None:
    bins = list(dict.fromkeys(r["BIN"] for r in rows))
    per_sample: dict[str, dict] = {}
    for r in rows:
        d = per_sample.setdefault(r["SAMPLE"], {"CALL": r["CALL"], "MARGIN": r["MARGIN_PCT_POINTS"], "FLAG": r["FLAG"]})
        d[r["BIN"]] = r["PCT_OF_ASSIGNED"]
    with open(path, "w") as fh:
        fh.write("# id: 'subtype_estimate'\n")
        fh.write("# section_name: 'Estimated HIV-1 subtype (read-mapping based)'\n")
        fh.write("# description: '% of reads mapped unambiguously to each panel bin (A, B, M = group M not assigned to A or B). Research use only; not a genotyping result.'\n")
        fh.write("# plot_type: 'table'\n")
        cols = ["SAMPLE"] + [f"{b}_PCT" for b in bins] + ["CALL", "MARGIN", "FLAG"]
        fh.write("\t".join(cols) + "\n")
        for s, d in sorted(per_sample.items()):
            fh.write("\t".join([s] + [str(d.get(b, 0)) for b in bins] + [d["CALL"], str(d["MARGIN"]), d["FLAG"]]) + "\n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--sample", required=True)
    s.add_argument("--stats", required=True)
    s.add_argument("--primary-name", required=True, help="bin name BBSplit reports as 'primary'")
    s.add_argument("--bins", default="A,B,M")
    s.add_argument("--min-reads", type=int, default=100)
    s.add_argument("--min-margin", type=float, default=10.0)
    c = sub.add_parser("combine")
    c.add_argument("tables", nargs="+")
    c.add_argument("--out", required=True)
    c.add_argument("--mqc", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "sample":
        bins = [b for b in args.bins.split(",") if b]
        write(sample_rows(args.sample, args.stats, args.primary_name, bins, args.min_reads, args.min_margin), sys.stdout)
    else:
        rows = read_tables(args.tables)
        with open(args.out, "w") as fh:
            write(rows, fh)
        write_mqc(rows, args.mqc)


if __name__ == "__main__":
    main()
