#!/usr/bin/env python3
"""Validate the public viral iGenome catalog without downloading references."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "igenomes" / "manifest.json"


def test_manifest_entries_are_public_and_checksummed():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["schema_version"] == 1
    assert {"HIV1", "HCV", "SARS_COV_2", "INFLUENZA_A", "INFLUENZA_B", "RSV", "HBV"} <= set(manifest["entries"])
    for name, entry in manifest["entries"].items():
        reference = ROOT / entry["reference"]
        assert reference.is_file(), name
        digest = hashlib.sha256(reference.read_bytes()).hexdigest()
        assert digest == entry["sha256"], name
        assert entry["accessions"], name
        assert entry["source"], name


def test_optional_assets_are_real_files():
    manifest = json.loads(MANIFEST.read_text())
    for name, entry in manifest["entries"].items():
        for key in ("amplicons", "primer_bed", "annotation"):
            if key in entry:
                assert (ROOT / entry[key]).is_file(), (name, key)
