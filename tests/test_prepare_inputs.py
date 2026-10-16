#!/usr/bin/env python3
"""Stub tests for prepare_inputs.py / validate_only artefacts. Research use only."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "bin" / "prepare_inputs.py"
HIV_FASTA = ROOT / "assets" / "presets" / "hiv1" / "reference.fasta"
HIV_AMP = ROOT / "assets" / "presets" / "hiv1" / "amplicons.tsv"
SARS_FASTA = ROOT / "assets" / "presets" / "sars-cov-2" / "reference.fasta"
SARS_BED = ROOT / "assets" / "presets" / "sars-cov-2" / "primers.bed"
FLU_FASTA = ROOT / "assets" / "presets" / "influenza-a" / "reference.fasta"


def run(args: list[str], strict: bool = True) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(PREPARE), *args]
    if strict:
        cmd.append("--strict-exit")
    return subprocess.run(cmd, capture_output=True, text=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_hiv1_valid(tmp: Path) -> None:
    rc = run(
        [
            "--reference", str(HIV_FASTA),
            "--amplicons", str(HIV_AMP),
            "--preset", "hiv1",
            "--pipeline-version", "0.5.0",
            "--target-taxid", "11676",
            "--target-label", "HIV1",
            "--outdir", str(tmp),
        ]
    )
    assert rc.returncode == 0, rc.stderr
    val = load_json(tmp / "validation.json")
    assert val["valid"] is True
    assert val["errors"] == []
    mode = load_json(tmp / "run_mode.json")
    assert isinstance(mode["reference_accessions"], list)
    assert mode["reference_accessions"] == ["K03455|HIVHXB2CG"]
    assert mode["preset"] == "hiv1"
    assert mode["target_taxid"] == 11676
    annot = (tmp / "annotation_used.tsv").read_text().splitlines()
    header = annot[0].split("\t")
    assert "record" in header and "intervals" in header
    rows = [dict(zip(header, r.split("\t"))) for r in annot[1:]]
    by_prot = {r["protein"]: r for r in rows}
    assert by_prot["PR"]["intervals"] == "2253-2549"
    assert by_prot["RT"]["intervals"] == "2550-3869"
    assert by_prot["INT"]["intervals"] == "4230-5093"
    amp = (tmp / "amplicons_used.tsv").read_text().splitlines()[0].split("\t")
    assert amp == ["label", "protein", "reference", "5p_seq", "3p_seq", "start", "end"]
    fasta = (tmp / "reference_used.fasta").read_text()
    assert fasta.startswith(">K03455|HIVHXB2CG PR(Protease):")


def test_sars_bed_converter(tmp: Path) -> None:
    rc = run(
        [
            "--reference", str(SARS_FASTA),
            "--primer-bed", str(SARS_BED),
            "--preset", "sars-cov-2",
            "--target-taxid", "2697049",
            "--target-label", "SARS-CoV-2",
            "--outdir", str(tmp),
        ]
    )
    assert rc.returncode == 0, rc.stderr
    val = load_json(tmp / "validation.json")
    assert val["valid"] is True, val["errors"]
    amps = (tmp / "amplicons_used.tsv").read_text().splitlines()
    assert len(amps) == 100  # header + 99 amplicons
    annot = (tmp / "annotation_used.tsv").read_text().splitlines()
    header = annot[0].split("\t")
    orf1ab = [dict(zip(header, r.split("\t"))) for r in annot[1:] if r.split("\t")[1] == "ORF1ab"][0]
    assert orf1ab["intervals"] == "266-13468;13468-21555"
    mode = load_json(tmp / "run_mode.json")
    assert mode["reference_accessions"] == ["MN908947.3"]


def test_flu_requires_primers(tmp: Path) -> None:
    rc = run(["--reference", str(FLU_FASTA), "--preset", "influenza-a", "--outdir", str(tmp)])
    assert rc.returncode == 1
    val = load_json(tmp / "validation.json")
    assert val["valid"] is False
    assert any(e["code"] == "AMP_OR_BED" for e in val["errors"])
    mode = load_json(tmp / "run_mode.json")
    assert isinstance(mode["reference_accessions"], list)
    assert len(mode["reference_accessions"]) == 8


def test_unpaired_bed_nonzero(tmp: Path) -> None:
    bed = ROOT / "tests" / "fixtures" / "unpaired.bed"
    rc = run(
        ["--reference", str(HIV_FASTA), "--primer-bed", str(bed), "--outdir", str(tmp)]
    )
    assert rc.returncode == 1
    val = load_json(tmp / "validation.json")
    assert val["valid"] is False
    assert any(e["code"] == "BED_UNPAIRED" for e in val["errors"])


def test_minus_strand_rejected(tmp: Path) -> None:
    fa = tmp / "tiny.fasta"
    gff = tmp / "minus.gff"
    amp = tmp / "amp.tsv"
    fa.write_text(">rec\n" + "A" * 99 + "\n")
    gff.write_text("rec\t.\tCDS\t1\t99\t.\t-\t0\tgene=X;product=x\n")
    amp.write_text("label\tprotein\treference\t5p_seq\t3p_seq\tstart\tend\nA\tX\trec\tAAA\tTTT\t1\t30\n")
    rc = run(
        ["--reference", str(fa), "--amplicons", str(amp), "--annotation", str(gff), "--outdir", str(tmp / "out")]
    )
    assert rc.returncode == 1
    val = load_json(tmp / "out" / "validation.json")
    assert any(e["code"] == "CDS_UNSUPPORTED" for e in val["errors"])


def test_ref_too_large(tmp: Path) -> None:
    fa = tmp / "big.fasta"
    fa.write_text(">big Dummy(dummy):1-100001\n" + "A" * 100001 + "\n")
    amp = tmp / "amp.tsv"
    amp.write_text("label\tprotein\treference\t5p_seq\t3p_seq\tstart\tend\nA\tall\tbig\tAAA\tTTT\t1\t10\n")
    rc = run(["--reference", str(fa), "--amplicons", str(amp), "--outdir", str(tmp / "out")])
    assert rc.returncode == 1
    val = load_json(tmp / "out" / "validation.json")
    assert any(e["code"] == "REF_TOO_LARGE" for e in val["errors"])


def test_unknown_protein(tmp: Path) -> None:
    rc = run(
        [
            "--reference", str(HIV_FASTA),
            "--amplicons", str(HIV_AMP),
            "--protein", "NEF",
            "--outdir", str(tmp),
        ]
    )
    assert rc.returncode == 1
    val = load_json(tmp / "validation.json")
    assert any("no annotation for --protein NEF" in e["message"] for e in val["errors"])


def test_no_strict_exit_still_zero(tmp: Path) -> None:
    rc = run(
        ["--reference", str(FLU_FASTA), "--preset", "influenza-a", "--outdir", str(tmp)],
        strict=False,
    )
    assert rc.returncode == 0
    assert load_json(tmp / "validation.json")["valid"] is False


def main() -> int:
    tests = [
        test_hiv1_valid,
        test_sars_bed_converter,
        test_flu_requires_primers,
        test_unpaired_bed_nonzero,
        test_minus_strand_rejected,
        test_ref_too_large,
        test_unknown_protein,
        test_no_strict_exit_still_zero,
    ]
    failed = 0
    for fn in tests:
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(Path(td))
                print(f"ok  {fn.__name__}")
            except Exception as exc:
                failed += 1
                print(f"FAIL {fn.__name__}: {exc}")
    if failed:
        print(f"{failed} failed")
        return 1
    print(f"{len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
