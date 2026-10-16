#!/usr/bin/env python3
"""Stub tests for contamination_summary.py. Research use only."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))
from contamination_summary import sample_row  # noqa: E402

# Clade fragments: unclassified 10, root 90, Viruses 80, SARS-CoV-2 40,
# HIV-1 20, phiX 10, human 5, bacteria 5. Total fragments = 100.
REPORT = (
    "10.00\t10\t10\tU\t0\tunclassified\n"
    "90.00\t90\t0\tR\t1\troot\n"
    "80.00\t80\t0\tD\t10239\tViruses\n"
    "40.00\t40\t40\tS\t2697049\tSevere acute respiratory syndrome coronavirus 2\n"
    "20.00\t20\t20\tS\t11676\tHuman immunodeficiency virus 1\n"
    "10.00\t10\t10\tS\t10847\tEscherichia virus phiX174\n"
    "5.00\t5\t5\tS\t9606\tHomo sapiens\n"
    "5.00\t5\t5\tD\t2\tBacteria\n"
)


def test_other_viral_subtracts_target_not_hiv() -> None:
    with tempfile.TemporaryDirectory() as td:
        report = Path(td) / "report.txt"
        report.write_text(REPORT)
        sars = sample_row("S", str(report), 2697049, "SARS-CoV-2", 50.0, 50.0)
        hiv = sample_row("S", str(report), 11676, "HIV1", 50.0, 50.0)
        none = sample_row("S", str(report), None, "TARGET", 50.0, 50.0)

    # HIV1_* columns always use taxid 11676
    assert sars["HIV1_PCT"] == 20.0
    assert hiv["HIV1_PCT"] == 20.0
    assert none["HIV1_PCT"] == 20.0
    assert sars["HIV1_PCT_OF_CLASSIFIED"] == hiv["HIV1_PCT_OF_CLASSIFIED"]

    # other viral = viruses - target clade - phiX
    assert sars["OTHER_VIRAL_PCT"] == 30.0  # 80 - 40 - 10
    assert hiv["OTHER_VIRAL_PCT"] == 50.0   # 80 - 20 - 10 (hiv1 preset unchanged)
    assert none["OTHER_VIRAL_PCT"] == 70.0  # 80 - 0 - 10
    assert sars["TARGET_PCT"] == 40.0
    assert hiv["TARGET_PCT"] == 20.0
    assert hiv["HIV1_PCT"] == hiv["TARGET_PCT"]


def main() -> int:
    tests = [test_other_viral_subtracts_target_not_hiv]
    failed = 0
    for fn in tests:
        try:
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
