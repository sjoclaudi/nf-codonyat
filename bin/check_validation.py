#!/usr/bin/env python3
"""Exit 1 when reference/validation.json has valid=false. Research use only."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "validation.json")
    result = json.loads(path.read_text())
    def emit(msg: str) -> None:
        print(msg, file=sys.stdout)
        print(msg, file=sys.stderr)

    if result.get("valid"):
        emit("Validation passed")
        return 0
    emit("Validation failed. Errors:")
    for err in result.get("errors") or []:
        emit(f"  [{err.get('code')}] {err.get('message')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
