#!/usr/bin/env python3
"""Preset FASTA/BED consistency and prepare_inputs load tests. Research use only."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "bin" / "prepare_inputs.py"
PRESETS = ROOT / "assets" / "presets"

BUNDLED = ["hiv1", "sars-cov-2", "influenza-a", "influenza-b", "rsv", "hbv", "hcv"]


def run(args: list[str], strict: bool = True) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(PREPARE), *args]
    if strict:
        cmd.append("--strict-exit")
    return subprocess.run(cmd, capture_output=True, text=True)


def fasta_ids_and_lens(path: Path) -> dict[str, int]:
    rec: dict[str, int] = {}
    rid = None
    n = 0
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if rid is not None:
                rec[rid] = n
            rid = line[1:].split()[0]
            n = 0
        else:
            n += len(line.strip())
    if rid is not None:
        rec[rid] = n
    return rec


def parse_yml_accessions(path: Path) -> list[str]:
    acc: list[str] = []
    in_list = False
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip() == "reference_accessions:":
            in_list = True
            continue
        if in_list:
            s = line.strip()
            if s.startswith("- "):
                acc.append(s[2:].strip().strip("'\""))
            elif s and not s.startswith("-"):
                break
    return acc


def test_every_preset_directory_complete() -> None:
    for name in BUNDLED:
        d = PRESETS / name
        assert (d / "preset.yml").is_file(), name
        assert (d / "reference.fasta").is_file(), name
        assert (d / "SOURCES.md").is_file(), name
        src = (d / "SOURCES.md").read_text().lower()
        assert "research use only" in src, name
        for banned in ("resist", "clinical interpret", "drug-resist"):
            assert banned not in src, (name, banned)


def test_bed_chroms_and_coords_in_fasta() -> None:
    for name in BUNDLED:
        d = PRESETS / name
        recs = fasta_ids_and_lens(d / "reference.fasta")
        bed = d / "primers.bed"
        amp = d / "amplicons.tsv"
        if bed.is_file():
            n = 0
            for i, line in enumerate(bed.read_text().splitlines(), 1):
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split("\t")
                assert len(parts) >= 6, (name, i, len(parts))
                chrom, start_s, end_s, pname, _pool, strand = parts[:6]
                start, end = int(start_s), int(end_s)
                assert chrom in recs, (name, chrom, i)
                slen = recs[chrom]
                assert 0 <= start < end <= slen, (name, pname, start, end, slen)
                assert strand in "+-", (name, pname, strand)
                assert pname.endswith("_LEFT") or pname.endswith("_RIGHT"), (name, pname)
                n += 1
            assert n >= 2, name
        elif amp.is_file():
            assert name == "hiv1"
        else:
            assert name in {"hcv", "influenza-b"}


def test_preset_yml_accessions_match_fasta() -> None:
    for name in BUNDLED:
        d = PRESETS / name
        recs = list(fasta_ids_and_lens(d / "reference.fasta"))
        yml = parse_yml_accessions(d / "preset.yml")
        assert recs == yml, (name, recs, yml)


def test_each_preset_loads(tmp_path: Path) -> None:
    for name in BUNDLED:
        d = PRESETS / name
        out = tmp_path / name
        args = ["--reference", str(d / "reference.fasta"), "--preset", name, "--outdir", str(out)]
        bed, amp = d / "primers.bed", d / "amplicons.tsv"
        if bed.is_file():
            args += ["--primer-bed", str(bed)]
        elif amp.is_file():
            args += ["--amplicons", str(amp)]
        rc = run(args)
        assert rc.returncode == 0, f"{name}: {rc.stderr}"
        val = json.loads((out / "validation.json").read_text())
        assert val["valid"] is True, (name, val["errors"])
        mode = json.loads((out / "run_mode.json").read_text())
        assert mode["preset"] == name
        assert mode["reference_accessions"] == list(fasta_ids_and_lens(d / "reference.fasta"))
        annot = (out / "annotation_used.tsv").read_text().splitlines()
        assert len(annot) > 1, name


def test_hcv_and_ibv_load_without_primers(tmp_path: Path) -> None:
    for name in ("hcv", "influenza-b"):
        d = PRESETS / name
        out = tmp_path / f"{name}_nop"
        rc = run(
            [
                "--reference",
                str(d / "reference.fasta"),
                "--preset",
                name,
                "--outdir",
                str(out),
            ]
        )
        assert rc.returncode == 0, rc.stderr
        val = json.loads((out / "validation.json").read_text())
        assert val["valid"] is True, val["errors"]
        assert any(w["code"] == "NO_PRIMERS" for w in val["warnings"])
        amp = (out / "amplicons_used.tsv").read_text().splitlines()
        assert amp == ["label\tprotein\treference\t5p_seq\t3p_seq\tstart\tend"] or amp[
            0
        ].split("\t") == ["label", "protein", "reference", "5p_seq", "3p_seq", "start", "end"]
        assert len(amp) == 1


def test_hbv_origin_crossing_amplicon(tmp_path: Path) -> None:
    d = PRESETS / "hbv"
    out = tmp_path / "hbv"
    rc = run(
        [
            "--reference",
            str(d / "reference.fasta"),
            "--primer-bed",
            str(d / "primers.bed"),
            "--preset",
            "hbv",
            "--outdir",
            str(out),
        ]
    )
    assert rc.returncode == 0, rc.stderr
    val = json.loads((out / "validation.json").read_text())
    assert val["valid"] is True, val["errors"]
    assert not any(e["code"] == "BED_ORDER" for e in val["errors"])
    annot = (out / "annotation_used.tsv").read_text().splitlines()
    header = annot[0].split("\t")
    rows = [dict(zip(header, r.split("\t"))) for r in annot[1:]]
    by_prot = {r["protein"]: r for r in rows}
    assert by_prot["P"]["intervals"] == "2307-3221;1-1623"
    assert by_prot["L"]["intervals"] == "2854-3221;1-835"
    amps = (out / "amplicons_used.tsv").read_text().splitlines()
    labels = [r.split("\t")[0] for r in amps[1:]]
    assert "f3d7635a_5" in labels
    wrap = next(r.split("\t") for r in amps[1:] if r.startswith("f3d7635a_5\t"))
    # start (left.end+1) > end (right.start) for the origin-crossing pair
    assert int(wrap[5]) > int(wrap[6])


def main() -> int:
    tests = [
        test_every_preset_directory_complete,
        test_bed_chroms_and_coords_in_fasta,
        test_preset_yml_accessions_match_fasta,
        test_each_preset_loads,
        test_hcv_and_ibv_load_without_primers,
        test_hbv_origin_crossing_amplicon,
    ]
    failed = 0
    for fn in tests:
        try:
            if fn.__code__.co_argcount:
                with tempfile.TemporaryDirectory() as td:
                    fn(Path(td))
            else:
                fn()
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
