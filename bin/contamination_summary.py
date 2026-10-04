#!/usr/bin/env python3
"""Summarise Kraken2 reports into a contamination QC table (report-only).

Per sample:
    contamination_summary.py sample --sample S --report S.kraken2.report.txt \
        --warn-hiv-pct 50 --warn-human-pct 50 > S.contamination.tsv
Combine:
    contamination_summary.py combine S1.contamination.tsv ... \
        --out contamination_summary.tsv --mqc contamination_mqc.tsv

Percentages are of all read fragments given to Kraken2 (a read pair counts once).
The warning flag is informative only: no reads are removed and nothing is stopped.
Research use only.
"""

from __future__ import annotations

import argparse
import sys

HIV1, PHIX, HUMAN, VIRUSES, BACTERIA = 11676, 10847, 9606, 10239, 2

COLUMNS = [
    "SAMPLE", "TOTAL_FRAGMENTS", "UNCLASSIFIED_PCT", "CLASSIFIED_PCT", "HIV1_PCT", "HIV1_PCT_OF_CLASSIFIED",
    "HUMAN_PCT", "PHIX_PCT", "BACTERIA_PCT", "OTHER_VIRAL_PCT", "OTHER_PCT", "WARNING",
]


def read_report(path: str) -> tuple[int, dict[int, int]]:
    """Return (unclassified fragments, {taxid: clade fragments}) from a Kraken2 report."""
    unclassified = 0
    clade: dict[int, int] = {}
    with open(path) as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            reads, taxid = int(parts[1]), int(parts[4])
            if taxid == 0:
                unclassified = reads
            else:
                clade[taxid] = reads
    return unclassified, clade


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 3) if d else 0.0


def sample_row(sample: str, report: str, warn_hiv: float, warn_human: float) -> dict:
    unclassified, clade = read_report(report)
    classified = clade.get(1, 0)
    total = unclassified + classified
    hiv, phix, human = clade.get(HIV1, 0), clade.get(PHIX, 0), clade.get(HUMAN, 0)
    viruses, bacteria = clade.get(VIRUSES, 0), clade.get(BACTERIA, 0)
    other_viral = max(0, viruses - hiv - phix)
    other = max(0, classified - viruses - human - bacteria)
    hiv_of_classified = pct(hiv, classified)
    human_pct = pct(human, total)
    warnings = []
    if total == 0:
        warnings.append("no_reads")
    else:
        if hiv_of_classified < warn_hiv:
            warnings.append(f"HIV1<{warn_hiv:g}%_of_classified")
        if human_pct > warn_human:
            warnings.append(f"human>{warn_human:g}%")
    return {
        "SAMPLE": sample,
        "TOTAL_FRAGMENTS": total,
        "UNCLASSIFIED_PCT": pct(unclassified, total),
        "CLASSIFIED_PCT": pct(classified, total),
        "HIV1_PCT": pct(hiv, total),
        "HIV1_PCT_OF_CLASSIFIED": hiv_of_classified,
        "HUMAN_PCT": human_pct,
        "PHIX_PCT": pct(phix, total),
        "BACTERIA_PCT": pct(bacteria, total),
        "OTHER_VIRAL_PCT": pct(other_viral, total),
        "OTHER_PCT": pct(other, total),
        "WARNING": ";".join(warnings) or "none",
    }


def write_rows(rows: list[dict], out) -> None:
    out.write("\t".join(COLUMNS) + "\n")
    for row in rows:
        out.write("\t".join(str(row[c]) for c in COLUMNS) + "\n")


def read_rows(paths: list[str]) -> list[dict]:
    rows = []
    for path in paths:
        with open(path) as fh:
            header = fh.readline().rstrip("\n").split("\t")
            for line in fh:
                if line.strip():
                    rows.append(dict(zip(header, line.rstrip("\n").split("\t"))))
    return sorted(rows, key=lambda r: r["SAMPLE"])


def write_mqc(rows: list[dict], path: str) -> None:
    with open(path, "w") as fh:
        fh.write("# id: 'contamination'\n")
        fh.write("# section_name: 'Contamination check (Kraken2, report-only)'\n")
        fh.write("# description: '% of read fragments per group from Kraken2. Informative QC only; no reads are removed. Research use only.'\n")
        fh.write("# plot_type: 'table'\n")
        cols = ["SAMPLE", "HIV1_PCT", "HIV1_PCT_OF_CLASSIFIED", "HUMAN_PCT", "PHIX_PCT", "BACTERIA_PCT",
                "OTHER_VIRAL_PCT", "UNCLASSIFIED_PCT", "WARNING"]
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(str(r[c]) for c in cols) + "\n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--sample", required=True)
    s.add_argument("--report", required=True)
    s.add_argument("--warn-hiv-pct", type=float, default=50.0)
    s.add_argument("--warn-human-pct", type=float, default=50.0)
    c = sub.add_parser("combine")
    c.add_argument("tables", nargs="+")
    c.add_argument("--out", required=True)
    c.add_argument("--mqc", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "sample":
        write_rows([sample_row(args.sample, args.report, args.warn_hiv_pct, args.warn_human_pct)], sys.stdout)
    else:
        rows = read_rows(args.tables)
        with open(args.out, "w") as fh:
            write_rows(rows, fh)
        write_mqc(rows, args.mqc)


if __name__ == "__main__":
    main()
