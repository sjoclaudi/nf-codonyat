#!/usr/bin/env python3
"""Validate reference, primers and annotation for nf-codonyat.

Thin wrapper around prepare_inputs.py --strict-exit. Writes validation.json
and the reference/ artefacts; exits non-zero on failure.

Research use only.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Same directory as this script (Nextflow stages bin/ onto PATH)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_inputs import main as prepare_main  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--strict-exit" not in argv:
        argv.append("--strict-exit")
    if "--out" in argv:
        # compatibility with the earlier CLI
        i = argv.index("--out")
        out = argv[i + 1]
        del argv[i : i + 2]
        argv.extend(["--outdir", str(Path(out).parent)])
    return prepare_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
