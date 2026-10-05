#!/usr/bin/env python3
"""Per-position strand metrics: merged-read alignment vs the unmerged (pre-merge) read alignment.

    strand_metrics.py --sample S --merged S.tsv --unmerged S.unmerged.tsv > S.strand_metrics_unmerged.tsv

After BBMerge, a merged read is one fragment written in R1's orientation, so the
FWCOV/RVCOV/RATIO of the main codonyat table describe fragment orientation. The
same reads aligned as ordinary pairs before merging give classic read-strand
metrics; both are reported side by side. Research use only.
"""

from __future__ import annotations

import argparse
import csv
import sys

COLUMNS = ["SAMPLE", "PROTEIN", "POSITION", "FWCOV", "RVCOV", "TOTALCOV", "RATIO",
           "FWCOV_UNMERGED", "RVCOV_UNMERGED", "TOTALCOV_UNMERGED", "RATIO_UNMERGED"]


def per_position(path: str) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    with open(path) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out.setdefault((r["PROTEIN"], int(r["POSITION"])), r)
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", required=True)
    ap.add_argument("--merged", required=True)
    ap.add_argument("--unmerged", required=True)
    args = ap.parse_args(argv)
    merged, unmerged = per_position(args.merged), per_position(args.unmerged)
    out = sys.stdout
    out.write("\t".join(COLUMNS) + "\n")
    for key in sorted(set(merged) | set(unmerged)):
        m, u = merged.get(key, {}), unmerged.get(key, {})
        row = [args.sample, key[0], key[1],
               m.get("FWCOV", 0), m.get("RVCOV", 0), m.get("TOTALCOV", 0), m.get("RATIO", 0),
               u.get("FWCOV", 0), u.get("RVCOV", 0), u.get("TOTALCOV", 0), u.get("RATIO", 0)]
        out.write("\t".join(str(v) for v in row) + "\n")


if __name__ == "__main__":
    main()
