#!/usr/bin/env python3
"""Validate inputs and write reference/ + run_mode.json artefacts for nf-codonyat.

Always writes validation.json (even on failure). On success also writes:
  reference_used.fasta, annotation_used.tsv, amplicons_used.tsv, run_mode.json

Exit 0 always so Nextflow can publish validation.json; the workflow then fails
when valid is false. Use --strict-exit to exit non-zero on failure (CLI / tests).

Research use only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

MAX_REF_BP = 100_000
PROTEIN_PART_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9_.-]*)\((?P<desc>[^)]*)\):(?P<iv>.+)$"
)


@dataclass
class Issue:
    code: str
    file: str
    line: int | None
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "file": self.file, "line": self.line, "message": self.message}


@dataclass
class Interval:
    start: int
    end: int

    def length(self) -> int:
        return self.end - self.start + 1

    def fmt(self) -> str:
        return f"{self.start}-{self.end}"


@dataclass
class Protein:
    record: str
    name: str
    description: str
    intervals: list[Interval]
    strand: str = "+"
    source: str = "header"

    def intervals_semi(self) -> str:
        return ";".join(i.fmt() for i in self.intervals)

    def intervals_comma(self) -> str:
        return ",".join(i.fmt() for i in self.intervals)

    def nt_length(self) -> int:
        return sum(i.length() for i in self.intervals)

    def header_fragment(self) -> str:
        desc = self.description or self.name
        return f"{self.name}({desc}):{self.intervals_comma()}"


@dataclass
class Primer:
    chrom: str
    start: int
    end: int
    name: str
    pool: str
    strand: str
    line: int


@dataclass
class State:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    records: dict[str, str] = field(default_factory=dict)
    record_order: list[str] = field(default_factory=list)
    raw_headers: dict[str, str] = field(default_factory=dict)
    proteins: list[Protein] = field(default_factory=list)
    primers: list[Primer] = field(default_factory=list)
    amplicon_rows: list[dict] = field(default_factory=list)

    def err(self, code: str, file: str, message: str, line: int | None = None) -> None:
        self.errors.append(Issue(code, file, line, message))

    def warn(self, code: str, file: str, message: str, line: int | None = None) -> None:
        self.warnings.append(Issue(code, file, line, message))


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_fasta(path: Path, state: State) -> None:
    current_id = None
    current_header = None
    seq: list[str] = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if current_id is not None:
                    state.records[current_id] = "".join(seq).upper()
                    state.record_order.append(current_id)
                    state.raw_headers[current_id] = current_header or current_id
                current_header = line[1:].strip()
                current_id = current_header.split()[0] if current_header else ""
                seq = []
            else:
                seq.append(line.strip())
        if current_id is not None:
            state.records[current_id] = "".join(seq).upper()
            state.record_order.append(current_id)
            state.raw_headers[current_id] = current_header or current_id
    if not state.records:
        state.err("REF_EMPTY", str(path), "Reference FASTA is empty")
        return
    total = sum(len(s) for s in state.records.values())
    if total > MAX_REF_BP:
        state.err(
            "REF_TOO_LARGE",
            str(path),
            f"Reference total size {total} bp exceeds limit {MAX_REF_BP} bp",
        )


def parse_intervals(text: str, sep: str) -> list[Interval]:
    out = []
    for part in text.split(sep):
        part = part.strip()
        if not part:
            continue
        start_s, end_s = part.split("-", 1)
        out.append(Interval(int(start_s), int(end_s)))
    return out


def proteins_from_header(record_id: str, header: str) -> list[Protein]:
    """Parse codonyat FASTA header proteins: Name(Description):start-end,start-end;..."""
    # BioPython-style: description may start with the record id
    rest = header
    if rest.startswith(record_id):
        rest = rest[len(record_id) :].strip()
    proteins = []
    for part in rest.split(";"):
        part = part.strip()
        if not part:
            continue
        m = PROTEIN_PART_RE.match(part)
        if not m:
            continue
        intervals = parse_intervals(m.group("iv"), ",")
        # Header interval start > end is how a minus-strand CDS is written; not origin-crossing
        # (that is two intervals, each start <= end).
        minus = any(iv.start > iv.end for iv in intervals)
        proteins.append(
            Protein(
                record=record_id,
                name=m.group("name"),
                description=m.group("desc"),
                intervals=intervals,
                strand="-" if minus else "+",
                source="header",
            )
        )
    return proteins


def rc(seq: str) -> str:
    return seq.translate(str.maketrans("ACGTacgtNn", "TGCAtgcaNn"))[::-1]


def read_primer_bed(path: Path, state: State) -> None:
    with open(path) as fh:
        for i, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                state.err("BED_COLUMNS", str(path), f"expected at least 6 columns, got {len(parts)}", i)
                continue
            chrom, start_s, end_s, name, pool, strand = parts[:6]
            try:
                start, end = int(start_s), int(end_s)
            except ValueError:
                state.err("BED_COLUMNS", str(path), f"start/end are not integers: {start_s}, {end_s}", i)
                continue
            if strand not in "+-":
                state.err("BED_STRAND", str(path), f"strand must be + or -, got '{strand}'", i)
            state.primers.append(Primer(chrom, start, end, name, pool, strand, i))
    if not state.primers:
        state.err("BED_EMPTY", str(path), "Primer BED file is empty")


def primer_kind(name: str) -> tuple[str, str] | None:
    """Return (amplicon, LEFT|RIGHT) or None. Ignores _alt names that do not end with _LEFT/_RIGHT."""
    if name.endswith("_LEFT"):
        return name[: -len("_LEFT")], "LEFT"
    if name.endswith("_RIGHT"):
        return name[: -len("_RIGHT")], "RIGHT"
    return None


def validate_primers(bed_path: str, state: State) -> None:
    for p in state.primers:
        if p.chrom not in state.records:
            state.err("CHROM_MISMATCH", bed_path, f"Chromosome '{p.chrom}' in BED not found in reference", p.line)
            continue
        seq_len = len(state.records[p.chrom])
        if p.start < 0 or p.end > seq_len or p.start >= p.end:
            state.err(
                "BED_OUT_OF_RANGE",
                bed_path,
                f"{p.name} coordinates [{p.start}, {p.end}] out of range [0, {seq_len}]",
                p.line,
            )
        if primer_kind(p.name) is None:
            state.err("BED_NAMING", bed_path, f"Primer name '{p.name}' must end with _LEFT or _RIGHT", p.line)

    grouped: dict[str, dict[str, list[Primer]]] = defaultdict(lambda: {"LEFT": [], "RIGHT": []})
    for p in state.primers:
        kind = primer_kind(p.name)
        if kind:
            grouped[kind[0]][kind[1]].append(p)
    for amplicon, sides in grouped.items():
        if len(sides["LEFT"]) != 1:
            state.err("BED_UNPAIRED", bed_path, f"Amplicon '{amplicon}' has {len(sides['LEFT'])} LEFT primers (expected 1)")
        if len(sides["RIGHT"]) != 1:
            state.err("BED_UNPAIRED", bed_path, f"Amplicon '{amplicon}' has {len(sides['RIGHT'])} RIGHT primers (expected 1)")
        if len(sides["LEFT"]) == 1 and len(sides["RIGHT"]) == 1:
            left, right = sides["LEFT"][0], sides["RIGHT"][0]
            if left.chrom != right.chrom:
                state.err("BED_CHROM_MISMATCH", bed_path, f"Amplicon '{amplicon}' primers on different chromosomes")
            elif left.start >= right.end:
                state.err("BED_ORDER", bed_path, f"Amplicon '{amplicon}' LEFT primer not before RIGHT primer")


def bed_to_amplicon_rows(state: State) -> list[dict]:
    grouped: dict[str, dict[str, Primer]] = {}
    for p in state.primers:
        kind = primer_kind(p.name)
        if not kind:
            continue
        amp, side = kind
        grouped.setdefault(amp, {})[side] = p
    rows = []
    for amp in sorted(grouped):
        sides = grouped[amp]
        if "LEFT" not in sides or "RIGHT" not in sides:
            continue
        left, right = sides["LEFT"], sides["RIGHT"]
        if left.chrom not in state.records or left.chrom != right.chrom:
            continue
        seq = state.records[left.chrom]
        left_seq = seq[left.start : left.end]
        right_seq = seq[right.start : right.end]
        if left.strand == "-":
            left_seq = rc(left_seq)
        if right.strand == "-":
            right_seq = rc(right_seq)
        rows.append(
            {
                "label": amp,
                "protein": "all",
                "reference": left.chrom,
                "5p_seq": left_seq.upper(),
                "3p_seq": right_seq.upper(),
                "start": left.end + 1,
                "end": right.start,
            }
        )
    return rows


def read_amplicons_tsv(path: Path, state: State) -> None:
    with open(path) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if reader.fieldnames is None or len(reader.fieldnames) != 7:
            n = 0 if reader.fieldnames is None else len(reader.fieldnames)
            state.err(
                "AMP_COLUMNS",
                str(path),
                "Amplicons file must have 7 tab-separated columns "
                "(label,protein,reference,5p_seq,3p_seq,start,end); "
                f"found {n}",
            )
            return
        for i, row in enumerate(reader, 2):
            if not row or not any((v or "").strip() for v in row.values()):
                continue
            rec = (row.get("reference") or "").strip()
            if rec and rec not in state.records:
                state.err("CHROM_MISMATCH", str(path), f"Amplicon reference '{rec}' not in FASTA", i)
            state.amplicon_rows.append(row)


def parse_gff_proteins(path: Path, state: State) -> list[Protein]:
    grouped: dict[str, Protein] = {}
    order: list[str] = []
    with open(path) as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 9 or parts[2] != "CDS":
                continue
            seqid, start_s, end_s, strand, attrs_s = parts[0], parts[3], parts[4], parts[6], parts[8]
            attrs = {}
            for item in attrs_s.split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    attrs[k.strip()] = v.strip()
            name = attrs.get("gene") or attrs.get("Name") or attrs.get("product") or attrs.get("ID") or f"CDS_{i}"
            name = name.replace("%2C", ",").split()[0]
            key = attrs.get("ID") or f"{seqid}:{name}"
            try:
                iv = Interval(int(start_s), int(end_s))
            except ValueError:
                state.err("ANNOTATION_FORMAT", str(path), f"CDS coordinates are not integers on line {i}", i)
                continue
            if key not in grouped:
                grouped[key] = Protein(
                    record=seqid,
                    name=name,
                    description=attrs.get("product") or attrs.get("Note") or name,
                    intervals=[iv],
                    strand=strand,
                    source="gff",
                )
                order.append(key)
            else:
                grouped[key].intervals.append(iv)
    return [grouped[k] for k in order]


def parse_bed_annot(path: Path, state: State) -> list[Protein]:
    proteins = []
    with open(path) as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                state.err("ANNOTATION_FORMAT", str(path), "BED annotation needs 4 columns: chrom,start,end,name", i)
                continue
            chrom, start_s, end_s, name = parts[:4]
            proteins.append(
                Protein(
                    record=chrom,
                    name=name,
                    description=name,
                    intervals=[Interval(int(start_s) + 1, int(end_s))],
                    strand="+",
                    source="bed",
                )
            )
    return proteins


def parse_annot_tsv(path: Path) -> list[Protein]:
    proteins = []
    with open(path) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            strand = (row.get("strand") or "+").strip() or "+"
            proteins.append(
                Protein(
                    record=row["record"],
                    name=row["protein"],
                    description=row.get("description") or row["protein"],
                    intervals=parse_intervals(row["intervals"], ";"),
                    strand=strand,
                    source="tsv",
                )
            )
    return proteins


def validate_proteins(annot_path: str, state: State) -> None:
    for p in state.proteins:
        if p.strand == "-" or any(iv.start > iv.end for iv in p.intervals):
            state.err("CDS_UNSUPPORTED", annot_path, f"CDS '{p.name}' on minus strand not supported")
            continue
        if any(c in p.name for c in "(:;"):
            state.err("CDS_INVALID_NAME", annot_path, f"CDS name '{p.name}' contains forbidden characters (, : or ;")
        if p.record not in state.records:
            state.err("CHROM_MISMATCH", annot_path, f"CDS '{p.name}' on sequence '{p.record}' not in reference")
            continue
        seq_len = len(state.records[p.record])
        for iv in p.intervals:
            if iv.start < 1 or iv.end > seq_len:
                # origin-crossing is two intervals, each with start <= end
                state.err(
                    "CDS_OUT_OF_RANGE",
                    annot_path,
                    f"CDS '{p.name}' coordinates [{iv.start}, {iv.end}] out of range [1, {seq_len}]",
                )
        if p.nt_length() % 3 != 0:
            state.err(
                "CDS_NOT_MULTIPLE_OF_3",
                annot_path,
                f"CDS '{p.name}' joined length {p.nt_length()} not divisible by 3",
            )


def amplicon_overlaps_cds(state: State) -> None:
    if not state.amplicon_rows or not state.proteins:
        return
    if any(e.code.startswith("CDS_") for e in state.errors):
        return
    for row in state.amplicon_rows:
        try:
            a0, a1 = int(row["start"]), int(row["end"])
        except (KeyError, ValueError, TypeError):
            continue
        rec = row.get("reference")
        overlaps = False
        for p in state.proteins:
            if p.record != rec:
                continue
            for iv in p.intervals:
                if not (a1 < iv.start or a0 > iv.end):
                    overlaps = True
                    break
        if not overlaps:
            state.err(
                "AMPLICON_NO_CDS",
                "amplicons",
                f"Amplicon '{row.get('label')}' does not overlap any CDS",
            )


def write_fasta(path: Path, state: State) -> None:
    with open(path, "w") as fh:
        for rid in state.record_order:
            seq = state.records[rid]
            rec_proteins = [p for p in state.proteins if p.record == rid]
            if rec_proteins:
                annot = ";".join(p.header_fragment() for p in rec_proteins)
                fh.write(f">{rid} {annot}\n")
            else:
                fh.write(f">{state.raw_headers.get(rid, rid)}\n")
            for i in range(0, len(seq), 70):
                fh.write(seq[i : i + 70] + "\n")


def write_annotation_used(path: Path, state: State) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "record",
                "protein",
                "description",
                "intervals",
                "strand",
                "start",
                "end",
                "length_aa",
                "source",
            ],
            delimiter="\t",
            lineterminator="\n",
        )
        w.writeheader()
        for p in state.proteins:
            w.writerow(
                {
                    "record": p.record,
                    "protein": p.name,
                    "description": p.description,
                    "intervals": p.intervals_semi(),
                    "strand": p.strand,
                    "start": p.intervals[0].start if p.intervals else "",
                    "end": p.intervals[-1].end if p.intervals else "",
                    "length_aa": p.nt_length() // 3 if p.nt_length() % 3 == 0 else "",
                    "source": p.source,
                }
            )


def write_amplicons_used(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["label", "protein", "reference", "5p_seq", "3p_seq", "start", "end"],
            delimiter="\t",
            lineterminator="\n",
        )
        w.writeheader()
        for row in rows:
            w.writerow(row)


def write_run_mode(path: Path, args: argparse.Namespace, state: State) -> None:
    def _bool(v) -> bool:
        return str(v).lower() in {"true", "1", "yes"}

    kraken_skipped = _bool(args.kraken2_skipped)
    payload = {
        "pipeline_version": args.pipeline_version,
        "preset": args.preset,
        "target_taxid": int(args.target_taxid) if str(args.target_taxid) not in {"", "null", "None"} else None,
        "target_label": args.target_label or None,
        "reference_accessions": list(state.record_order),
        "reference_sha256": sha256_file(args.reference),
        "primer_file_sha256": sha256_file(args.primer_bed) or sha256_file(args.amplicons),
        "annotation_sha256": sha256_file(args.annotation),
        "kraken2_skipped": kraken_skipped,
        "kraken2_skip_reason": args.kraken2_skip_reason or None,
        "subtype_skipped": _bool(args.subtype_skipped),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def load_annotation(args: argparse.Namespace, state: State) -> str:
    """Populate state.proteins. Returns the annotation source path used in error messages."""
    if args.annotation:
        p = args.annotation
        name = p.name.lower()
        if name.endswith(".gff") or name.endswith(".gff3"):
            state.proteins = parse_gff_proteins(p, state)
        elif name.endswith(".bed"):
            state.proteins = parse_bed_annot(p, state)
        elif name.endswith(".tsv"):
            state.proteins = parse_annot_tsv(p)
        else:
            state.err("ANNOTATION_FORMAT", str(p), "Annotation must be .gff, .gff3, .bed or .tsv")
        return str(p)
    for rid in state.record_order:
        state.proteins.extend(proteins_from_header(rid, state.raw_headers[rid]))
    return str(args.reference)


def check_requested_proteins(protein_arg: str, annot_path: str, state: State) -> None:
    requested = [p.strip() for p in (protein_arg or "").split(",") if p.strip()]
    if not requested:
        state.err("PROTEIN_UNKNOWN", annot_path, "--protein is empty: give a protein name, a comma-separated list or 'all'")
        return
    if len(requested) > 1 and any(p.lower() == "all" for p in requested):
        state.err("PROTEIN_UNKNOWN", annot_path, f"--protein 'all' cannot be combined with other names (got: {protein_arg})")
        return
    if any(p.lower() == "all" for p in requested):
        return
    found = [p.name for p in state.proteins]
    missing = [p for p in requested if p not in found]
    if missing and found:
        state.err(
            "PROTEIN_UNKNOWN",
            annot_path,
            f"Reference header has no annotation for --protein {', '.join(missing)} (found: {', '.join(found)})",
        )
    elif missing:
        state.err(
            "PROTEIN_UNKNOWN",
            annot_path,
            f"Reference header has no annotation for --protein {', '.join(missing)}",
        )


def maybe_samplesheet(path: Path | None, state: State) -> None:
    if path is None:
        return
    with open(path) as fh:
        header = fh.readline()
        if "sample" not in header:
            state.err("SAMPLESHEET", str(path), "Samplesheet must have a 'sample' column", 1)
            return
        cols = [c.strip() for c in header.strip().split(",")]
        for i, line in enumerate(fh, 2):
            if not line.strip():
                continue
            row = dict(zip(cols, [c.strip() for c in line.strip().split(",")]))
            sample = row.get("sample")
            fq1, sam = row.get("fastq_1") or "", row.get("sam") or ""
            if not sample:
                state.err("SAMPLESHEET", str(path), "every row needs a 'sample' value", i)
            if (not fq1) == (not sam):
                state.err("SAMPLESHEET", str(path), f"sample '{sample}' must have either fastq_1 or sam (not both, not neither)", i)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reference", required=True, type=Path)
    ap.add_argument("--primer-bed", type=Path)
    ap.add_argument("--amplicons", type=Path)
    ap.add_argument("--annotation", type=Path)
    ap.add_argument("--samplesheet", type=Path)
    ap.add_argument("--preset", default="custom")
    ap.add_argument("--pipeline-version", default="0.5.0")
    ap.add_argument("--target-taxid", default="")
    ap.add_argument("--target-label", default="")
    ap.add_argument("--kraken2-skipped", default="false")
    ap.add_argument("--kraken2-skip-reason", default="")
    ap.add_argument("--subtype-skipped", default="false")
    ap.add_argument("--protein", default="all", help="Protein name, comma-separated list, or 'all'")
    ap.add_argument("--outdir", type=Path, default=Path("."))
    ap.add_argument("--strict-exit", action="store_true", help="Exit 1 when validation fails")
    args = ap.parse_args(argv)

    args.outdir.mkdir(parents=True, exist_ok=True)
    state = State()

    try:
        read_fasta(args.reference, state)
    except Exception as exc:
        state.err("REF_READ_ERROR", str(args.reference), f"Failed to read reference: {exc}")

    annot_path = load_annotation(args, state)
    if state.proteins:
        validate_proteins(annot_path, state)
    elif not state.errors:
        state.warn("NO_ANNOTATION", annot_path, "No protein annotations found in FASTA header or --annotation")

    if args.primer_bed and args.amplicons:
        state.err("AMP_XOR_BED", str(args.primer_bed), "Cannot specify both --amplicons and --primer-bed")
    elif args.primer_bed:
        try:
            read_primer_bed(args.primer_bed, state)
            validate_primers(str(args.primer_bed), state)
            if not any(e.code in {"BED_UNPAIRED", "BED_COLUMNS", "BED_EMPTY"} for e in state.errors):
                state.amplicon_rows = bed_to_amplicon_rows(state)
        except Exception as exc:
            state.err("BED_READ_ERROR", str(args.primer_bed), f"Failed to read primer BED: {exc}")
    elif args.amplicons:
        try:
            read_amplicons_tsv(args.amplicons, state)
        except Exception as exc:
            state.err("AMP_READ_ERROR", str(args.amplicons), f"Failed to read amplicons TSV: {exc}")
    else:
        state.err("AMP_OR_BED", "primers", "Must provide either --amplicons (TSV) or --primer-bed (6-column BED)")

    amplicon_overlaps_cds(state)
    maybe_samplesheet(args.samplesheet, state)

    check_requested_proteins(args.protein, annot_path, state)

    valid = not state.errors
    validation = {
        "valid": valid,
        "errors": [e.to_dict() for e in state.errors],
        "warnings": [w.to_dict() for w in state.warnings],
    }
    (args.outdir / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")

    # Always write the published artefacts so PREPARE_REFERENCE can exit 0 and
    # Nextflow still stages validation.json + reference/ + run_mode.json.
    write_fasta(args.outdir / "reference_used.fasta", state)
    write_annotation_used(args.outdir / "annotation_used.tsv", state)
    write_amplicons_used(args.outdir / "amplicons_used.tsv", state.amplicon_rows)
    write_run_mode(args.outdir / "run_mode.json", args, state)

    if not valid:
        print(f"Validation failed with {len(state.errors)} error(s)", file=sys.stderr)
        for err in state.errors:
            print(f"  [{err.code}] {err.message}", file=sys.stderr)
        return 1 if args.strict_exit else 0
    print("Validation passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
