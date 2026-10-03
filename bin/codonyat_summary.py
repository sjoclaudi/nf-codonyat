#!/usr/bin/env python3
"""
codonyat_summary.py

Merges per-sample codonyat TSV files into a single combined TSV.
Adds a `SAMPLE` column so results from different samples can be distinguished.

Usage:
    codonyat_summary.py sample1.tsv sample2.tsv ... > codonyat_summary.tsv

Input TSV format (codonyat output):
    FILE | REFERENCE | PROTEIN | VARIANT | POSITION | FREQ | FWCOV | RVCOV | TOTALCOV | RATIO

Output TSV format: same columns + SAMPLE prepended.
"""

import sys
import csv
from pathlib import Path

HEADER = [
    "SAMPLE", "FILE", "REFERENCE", "PROTEIN", "VARIANT",
    "POSITION", "FREQ", "FWCOV", "RVCOV", "TOTALCOV", "RATIO"
]


def detect_dialect(path: Path) -> csv.Dialect:
    """Sniff the delimiter (tab vs comma) used in a TSV."""
    with open(path, newline="") as fh:
        sample = fh.read(4096)
    if "\t" in sample:
        return csv.excel_tab
    return csv.excel


def merge_tsvs(tsv_paths: list[str]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=HEADER, delimiter="\t")
    writer.writeheader()

    for tsv_path in tsv_paths:
        path = Path(tsv_path)
        if not path.exists() or path.stat().st_size == 0:
            continue

        sample = path.stem  # e.g. "sample1" from "sample1.tsv"
        dialect = detect_dialect(path)

        with open(path, newline="") as fh:
            reader = csv.DictReader(fh, delimiter=dialect.delimiter)
            for row in reader:
                row["SAMPLE"] = sample
                writer.writerow({k: row.get(k, "") for k in HEADER})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write(
            f"Usage: {sys.argv[0]} sample1.tsv [sample2.tsv ...]\n"
        )
        sys.exit(1)

    merge_tsvs(sys.argv[1:])
