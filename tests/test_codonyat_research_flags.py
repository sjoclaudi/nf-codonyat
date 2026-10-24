#!/usr/bin/env python3
"""Default research flags leave codon TSV/XML byte-identical.

codonyat 1.3.1: --min-freq / --min-coverage / --sb-alpha only affect stats/AAVF
flags (defaults 0.01 / 10 / 0.05). --min-baseq is off when omitted and changes
counts when set. The pipeline does not pass those three unless emit_stats or
emit_aavf is on, and does not pass --min-baseq when null.

This proves the hiv1 testdata SAM and the test_sarscov2 / test_flua references
(prepared like those profiles) stay byte-identical under the default extra
flags. Research use only.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "bin" / "prepare_inputs.py"
RUNNER = shutil.which("codonyat-runner") or str(Path.home() / ".local/bin/codonyat-runner")
MODULE = ROOT / "modules" / "local" / "codonyat" / "run" / "main.nf"

RATIO_UPPER = "3.16227766"
RATIO_LOWER = "0.316227766"


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def run_runner(sam: Path, ref: Path, amplicons: Path, out_prefix: Path, extra: list[str]) -> None:
    cmd = [
        RUNNER,
        str(sam),
        str(ref),
        str(amplicons),
        "--protein",
        "all",
        "--ratio-upper",
        RATIO_UPPER,
        "--ratio-lower",
        RATIO_LOWER,
        "--entropy-threshold",
        "0.0",
        "--csv-path",
        str(out_prefix.with_suffix(".tsv")),
        "--xml-path",
        str(out_prefix.with_suffix(".xml")),
        *extra,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def read_fasta(path: Path) -> dict[str, str]:
    recs: dict[str, str] = {}
    name = None
    seq: list[str] = []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if name:
                recs[name] = "".join(seq)
            name = line[1:].split()[0]
            seq = []
        else:
            seq.append(line.strip())
    if name:
        recs[name] = "".join(seq)
    return recs


def first_amplicon(amplicons: Path) -> tuple[str, int, int]:
    rows = amplicons.read_text().splitlines()
    header = rows[0].split("\t")
    idx = {name: i for i, name in enumerate(header)}
    row = rows[1].split("\t")
    return row[idx["reference"]], int(row[idx["start"]]), int(row[idx["end"]])


def write_covering_sam(dest: Path, fasta: Path, amplicons: Path) -> None:
    recs = read_fasta(fasta)
    chrom, start, end = first_amplicon(amplicons)
    assert chrom in recs, f"{chrom} not in {list(recs)}"
    seq = recs[chrom][start - 1 : end]
    assert seq, f"empty interval {chrom}:{start}-{end}"
    cigar = f"{len(seq)}M"
    qual = "I" * len(seq)
    lines = [
        "@HD\tVN:1.6\tSO:unsorted",
        f"@SQ\tSN:{chrom}\tLN:{len(recs[chrom])}",
    ]
    for i in range(12):
        lines.append(
            f"read{i}\t0\t{chrom}\t{start}\t60\t{cigar}\t*\t0\t0\t{seq}\t{qual}"
        )
    dest.write_text("\n".join(lines) + "\n")


def prepare(tmp: Path, args: list[str]) -> tuple[Path, Path]:
    out = tmp / "prep"
    out.mkdir(parents=True)
    cmd = [sys.executable, str(PREPARE), *args, "--outdir", str(out), "--strict-exit"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return out / "reference_used.fasta", out / "amplicons_used.tsv"


def assert_default_flags_identical(sam: Path, ref: Path, amplicons: Path, tmp: Path, label: str) -> None:
    base = tmp / f"{label}_base"
    flags = tmp / f"{label}_flags"
    run_runner(sam, ref, amplicons, base, [])
    run_runner(
        sam,
        ref,
        amplicons,
        flags,
        ["--min-freq", "0.01", "--min-coverage", "10", "--sb-alpha", "0.05"],
    )
    assert md5(base.with_suffix(".tsv")) == md5(flags.with_suffix(".tsv")), label
    assert md5(base.with_suffix(".xml")) == md5(flags.with_suffix(".xml")), label
    print(f"ok  {label} TSV/XML identical with default --min-freq/--min-coverage/--sb-alpha")


def test_module_does_not_pass_research_flags_unconditionally() -> None:
    text = MODULE.read_text()
    assert "min_baseq_arg = params.min_baseq != null" in text
    assert "research_on = params.emit_stats || params.emit_aavf" in text
    assert "research_args = research_on" in text
    command = text.split('"""')[1]
    assert "--collapsed-read-counts" not in command
    print("ok  test_module_does_not_pass_research_flags_unconditionally")


def test_hiv1_testdata(tmp_path: Path) -> None:
    sam = ROOT / "assets" / "testdata" / "sample1.sam"
    ref = ROOT / "assets" / "testdata" / "reference.fasta"
    amp = ROOT / "assets" / "testdata" / "amplicons.tsv"
    assert_default_flags_identical(sam, ref, amp, tmp_path, "hiv1")
    high = tmp_path / "hiv1_bq60"
    run_runner(sam, ref, amp, high, ["--min-baseq", "60"])
    base_tsv = tmp_path / "hiv1_base.tsv"
    assert md5(base_tsv) != md5(high.with_suffix(".tsv"))
    print("ok  hiv1 --min-baseq 60 changes TSV (null stays identical)")


def test_sarscov2_prepared(tmp_path: Path) -> None:
    ref, amp = prepare(
        tmp_path / "sars_prep",
        [
            "--reference",
            str(ROOT / "assets" / "testdata" / "sarscov2" / "reference.fasta"),
            "--primer-bed",
            str(ROOT / "assets" / "testdata" / "sarscov2" / "primers.bed"),
            "--annotation",
            str(ROOT / "assets" / "testdata" / "sarscov2" / "annotation.gff3"),
            "--preset",
            "custom",
        ],
    )
    sam = tmp_path / "sars.sam"
    write_covering_sam(sam, ref, amp)
    assert_default_flags_identical(sam, ref, amp, tmp_path, "test_sarscov2")


def test_influenza_b_no_primers_accepted(tmp_path: Path) -> None:
    """Cheap: prepare influenza-b with no BED and run codonyat-runner on a tiny SAM."""
    ref, amp = prepare(
        tmp_path / "ibv_prep",
        [
            "--reference",
            str(ROOT / "assets" / "presets" / "influenza-b" / "reference.fasta"),
            "--preset",
            "influenza-b",
        ],
    )
    rows = amp.read_text().splitlines()
    assert len(rows) == 9
    first = rows[1].split("\t")
    assert first[0].endswith("_full")
    assert first[5] == "1"
    sam = tmp_path / "ibv.sam"
    write_covering_sam(sam, ref, amp)
    run_runner(sam, ref, amp, tmp_path / "ibv", [])
    tsv = tmp_path / "ibv.tsv"
    assert tsv.is_file() and tsv.stat().st_size > 0
    print("ok  influenza-b no primers: placeholder amplicons accepted by codonyat 1.3.1")


def test_flua_prepared(tmp_path: Path) -> None:
    ref, amp = prepare(
        tmp_path / "flu_prep",
        [
            "--reference",
            str(ROOT / "assets" / "testdata" / "influenza" / "reference.fasta"),
            "--primer-bed",
            str(ROOT / "assets" / "testdata" / "influenza" / "primers.bed"),
            "--annotation",
            str(ROOT / "assets" / "testdata" / "influenza" / "annotation.bed"),
            "--preset",
            "custom",
        ],
    )
    sam = tmp_path / "flu.sam"
    write_covering_sam(sam, ref, amp)
    assert_default_flags_identical(sam, ref, amp, tmp_path, "test_flua")


def main() -> None:
    assert Path(RUNNER).exists(), f"codonyat-runner not found: {RUNNER}"
    test_module_does_not_pass_research_flags_unconditionally()
    with tempfile.TemporaryDirectory() as raw:
        tmp_path = Path(raw)
        test_hiv1_testdata(tmp_path)
        test_sarscov2_prepared(tmp_path)
        test_flua_prepared(tmp_path)
        test_influenza_b_no_primers_accepted(tmp_path)
    print("5 passed")


if __name__ == "__main__":
    main()
