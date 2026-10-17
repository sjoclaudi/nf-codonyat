#!/usr/bin/env python3
"""Keep assets/infra.json in sync with config, with no secrets in the UI payload.

The SaaS reads assets/infra.json for the read-only infra pane. It must show only:
  Kraken2 database name (last path component), resourceLimits, region,
  pipeline / container / codonyat versions.

Never include S3 URIs, bucket names or the AWS Batch queue. Values come from
config / module files, not a second hardcoded copy. Research use only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "assets" / "infra.json"
AWSBATCH = ROOT / "conf" / "awsbatch.config"
NFCONFIG = ROOT / "nextflow.config"
SCHEMA = ROOT / "nextflow_schema.json"
MODULE = ROOT / "modules" / "local" / "codonyat" / "run" / "main.nf"
ENV = ROOT / "modules" / "local" / "codonyat" / "run" / "environment.yml"

LIMITS_RE = re.compile(
    r"resourceLimits\s*=\s*\[cpus:\s*(\d+),\s*memory:\s*([0-9.]+)\.GB,\s*time:\s*(\d+)\.h\]"
)
REGION_RE = re.compile(r"^\s*region\s*=\s*'([^']+)'", re.M)
VERSION_RE = re.compile(r"^\s*version\s*=\s*'([^']+)'", re.M)
CONTAINER_RE = re.compile(r"container\s+'ghcr\.io/sjoclaudi/nf-codonyat:([^']+)'")
CODONYAT_RE = re.compile(r'codonyat==([0-9.]+)')
KRAKEN_NAME_RE = re.compile(r"infra\.kraken2_db_name\s*=\s*(\S+)")
FORBIDDEN = re.compile(
    r"s3://|awsbatch_queue|codonyat-queue|codonyat-nf-work|codonyat-refdb|codonyat/|bucket",
    re.I,
)


def limits_from_awsbatch() -> dict:
    match = LIMITS_RE.search(AWSBATCH.read_text())
    assert match, f"could not parse process.resourceLimits from {AWSBATCH}"
    return {
        "cpus": int(match.group(1)),
        "memory": f"{match.group(2)}.GB",
        "time": f"{match.group(3)}.h",
    }


def schema_xui() -> dict[str, str]:
    schema = json.loads(SCHEMA.read_text())
    out: dict[str, str] = {}
    for defn in schema["$defs"].values():
        for name, spec in defn.get("properties", {}).items():
            out[name] = spec["x-ui"]
    return out


def test_hidden_path_params_are_internal() -> None:
    xui = schema_xui()
    assert xui["awsbatch_queue"] == "internal"
    assert xui["kraken2_db"] == "internal"
    assert xui["kraken2_memory_mapping"] == "infra"
    print("ok  test_hidden_path_params_are_internal")


def test_infra_json_matches_config_and_hides_uris() -> None:
    infra = json.loads(INFRA.read_text())
    visible = json.dumps(
        {
            "kraken2_db_name": infra["kraken2_db_name"],
            "resourceLimits": infra["resourceLimits"],
            "region": infra["region"],
            "versions": infra["versions"],
        }
    )
    assert not FORBIDDEN.search(visible), "visible infra fields must not contain S3 URIs, buckets or the queue name"
    assert infra["x-ui"] == "infra"

    name = KRAKEN_NAME_RE.search(NFCONFIG.read_text())
    assert name, "nextflow.config must declare infra.kraken2_db_name"
    assert infra["kraken2_db_name"] == name.group(1)
    assert "/" not in infra["kraken2_db_name"]
    assert "s3:" not in infra["kraken2_db_name"]

    assert infra["resourceLimits"] == limits_from_awsbatch()
    region = REGION_RE.search(AWSBATCH.read_text())
    assert region, f"could not parse aws.region from {AWSBATCH}"
    assert infra["region"] == region.group(1)

    pipeline = VERSION_RE.search(NFCONFIG.read_text())
    container = CONTAINER_RE.search(MODULE.read_text())
    codonyat = CODONYAT_RE.search(ENV.read_text())
    assert pipeline and container and codonyat
    assert infra["versions"] == {
        "pipeline": pipeline.group(1),
        "container": container.group(1),
        "codonyat": codonyat.group(1),
    }
    assert set(infra) <= {
        "description",
        "x-ui",
        "kraken2_db_name",
        "resourceLimits",
        "region",
        "versions",
        "sources",
    }
    print("ok  test_infra_json_matches_config_and_hides_uris")


if __name__ == "__main__":
    test_hidden_path_params_are_internal()
    test_infra_json_matches_config_and_hides_uris()
    print("2 passed")
