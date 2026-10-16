#!/usr/bin/env python3
"""Run codonyat-runner for one protein, a comma-separated list, or 'all'.

codonyat 1.2.0 does not expand --protein all; this wrapper does, concatenating
per-protein TSV rows in annotation order so single-record HIV-1 tables stay
grouped PR then RT then INT (non-overlapping coordinates, sorted by position
within a protein — matching a one-pass write sorted by genomic position).

Research use only.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROTEIN_PART_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)\([^)]*\):")


def fasta_proteins(path: Path) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    with open(path) as fh:
        for line in fh:
            if not line.startswith(">"):
                continue
            for m in PROTEIN_PART_RE.finditer(line):
                name = m.group(1)
                if name not in seen:
                    seen.add(name)
                    names.append(name)
    return names


def merge_tsv(paths: list[Path], dest: Path) -> None:
    rows: list[dict] = []
    header: list[str] | None = None
    for p in paths:
        with open(p) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            if header is None:
                header = list(reader.fieldnames or [])
            for row in reader:
                rows.append(row)
    if header is None:
        dest.write_text("")
        return
    # Single-record: sort by POSITION then PROTEIN so HIV-1 matches a one-pass dump.
    def key(r: dict) -> tuple:
        try:
            pos = int(r.get("POSITION") or 0)
        except ValueError:
            pos = 0
        return (pos, r.get("PROTEIN") or "")

    rows.sort(key=key)
    # Match codonyat 1.2.0 write_csv (newline="" + DictWriter default \r\n) so
    # single-record HIV-1 tables stay byte-identical to v0.4.0 / 1.1.0.
    with open(dest, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header, delimiter="\t")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def merge_xml(named_paths: list[tuple[str, Path]], dest: Path) -> None:
    """Merge per-protein 1.2.0 XML into the 1.1.0 / v0.4.0 multi-protein layout.

    One protein → copy the flat SamContainer (same as 1.1.0 write_xml).
    Several proteins → wrap each protein's Position elements in
    ``<Protein name="X">`` in annotation order (1.1.0 write_xml_proteins).
    """
    import xml.etree.ElementTree as ET

    if not named_paths:
        dest.write_text("")
        return
    if len(named_paths) == 1:
        _name, only = named_paths[0]
        dest.write_bytes(only.read_bytes() if only.exists() else b"")
        return
    sample = ""
    reference = ""
    for _name, path in named_paths:
        if path.exists() and path.stat().st_size:
            src = ET.parse(path).getroot()
            sample = src.get("sample") or sample
            reference = src.get("reference") or reference
            break
    root = ET.Element("SamContainer", sample=sample, reference=reference)
    for name, path in named_paths:
        prot = ET.SubElement(root, "Protein", name=name)
        if path.exists() and path.stat().st_size:
            src = ET.parse(path).getroot()
            for pos in list(src.findall("Position")):
                prot.append(pos)
    ET.ElementTree(root).write(dest, encoding="utf-8", xml_declaration=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sam")
    ap.add_argument("reference")
    ap.add_argument("amplicons")
    ap.add_argument("--protein", default="all")
    ap.add_argument("--annotation", default="")
    ap.add_argument("--ratio-upper", required=True)
    ap.add_argument("--ratio-lower", required=True)
    ap.add_argument("--entropy-threshold", required=True)
    ap.add_argument("--csv-path", required=True)
    ap.add_argument("--xml-path", required=True)
    args = ap.parse_args()

    requested = [p.strip() for p in args.protein.split(",") if p.strip()]
    if not requested:
        print("--protein is empty", file=sys.stderr)
        return 1
    if any(p.lower() == "all" for p in requested) and len(requested) > 1:
        print("--protein 'all' cannot be combined with other names", file=sys.stderr)
        return 1
    if requested == ["all"] or (len(requested) == 1 and requested[0].lower() == "all"):
        proteins = fasta_proteins(Path(args.reference))
        if not proteins:
            print("No protein annotations found in the reference header", file=sys.stderr)
            return 1
    else:
        proteins = requested

    annot = ["--annotation", args.annotation] if args.annotation else []
    if len(proteins) == 1:
        cmd = [
            "codonyat-runner",
            args.sam,
            args.reference,
            args.amplicons,
            *annot,
            "--protein",
            proteins[0],
            "--ratio-upper",
            args.ratio_upper,
            "--ratio-lower",
            args.ratio_lower,
            "--entropy-threshold",
            args.entropy_threshold,
            "--csv-path",
            args.csv_path,
            "--xml-path",
            args.xml_path,
        ]
        return subprocess.call(cmd)

    tsvs, xmls = [], []
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        for name in proteins:
            csv_p = td_path / f"{name}.tsv"
            xml_p = td_path / f"{name}.xml"
            cmd = [
                "codonyat-runner",
                args.sam,
                args.reference,
                args.amplicons,
                *annot,
                "--protein",
                name,
                "--ratio-upper",
                args.ratio_upper,
                "--ratio-lower",
                args.ratio_lower,
                "--entropy-threshold",
                args.entropy_threshold,
                "--csv-path",
                str(csv_p),
                "--xml-path",
                str(xml_p),
            ]
            rc = subprocess.call(cmd)
            if rc != 0:
                return rc
            tsvs.append(csv_p)
            xmls.append(xml_p)
        merge_tsv(tsvs, Path(args.csv_path))
        merge_xml(list(zip(proteins, xmls)), Path(args.xml_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
