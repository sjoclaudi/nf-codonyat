#!/usr/bin/env python3
"""Keep assets/infra.json in sync with conf/awsbatch.config resourceLimits.

The SaaS reads assets/infra.json. Values must come from process.resourceLimits
in conf/awsbatch.config (16 CPU / 120 GB / 24 h), not a second hardcoded copy
that can drift. Research use only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "assets" / "infra.json"
AWSBATCH = ROOT / "conf" / "awsbatch.config"

LIMITS_RE = re.compile(
    r"resourceLimits\s*=\s*\[cpus:\s*(\d+),\s*memory:\s*([0-9.]+)\.GB,\s*time:\s*(\d+)\.h\]"
)


def limits_from_awsbatch() -> dict:
    text = AWSBATCH.read_text()
    match = LIMITS_RE.search(text)
    assert match, f"could not parse process.resourceLimits from {AWSBATCH}"
    return {
        "cpus": int(match.group(1)),
        "memory": f"{match.group(2)}.GB",
        "time": f"{match.group(3)}.h",
    }


def test_infra_json_matches_awsbatch_resource_limits() -> None:
    infra = json.loads(INFRA.read_text())
    assert infra["source"] == "conf/awsbatch.config process.resourceLimits"
    assert infra["x-ui"] == "infra"
    assert infra["resourceLimits"] == limits_from_awsbatch()
    assert infra["resourceLimits"] == {"cpus": 16, "memory": "120.GB", "time": "24.h"}


if __name__ == "__main__":
    test_infra_json_matches_awsbatch_resource_limits()
    print("ok  test_infra_json_matches_awsbatch_resource_limits")
    print("1 passed")
