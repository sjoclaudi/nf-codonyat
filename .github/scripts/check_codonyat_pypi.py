#!/usr/bin/env python3
"""Compare the pinned codonyat version against the latest PyPI release.

Reads the container/environment pins (Dockerfile and the local conda env)
and https://pypi.org/pypi/codonyat/json. When the pin is behind, writes a
GitHub warning annotation and a job-summary line, then exits 0 so the
check never fails the job for drift.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

PYPI_JSON = "https://pypi.org/pypi/codonyat/json"
PIN_RE = re.compile(r"codonyat==([0-9]+(?:\.[0-9]+)*)")
DEFAULT_PIN_FILES = (
    "Dockerfile",
    "modules/local/codonyat/run/environment.yml",
)


def parse_version(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def padded(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)), b + (0,) * (n - len(b))


def is_behind(pinned: str, latest: str) -> bool:
    left, right = padded(parse_version(pinned), parse_version(latest))
    return left < right


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "Dockerfile").is_file() and (parent / ".github").is_dir():
            return parent
    return Path.cwd()


def extract_pins(root: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    missing: list[str] = []
    for rel in DEFAULT_PIN_FILES:
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        matches = PIN_RE.findall(path.read_text())
        if not matches:
            raise SystemExit(f"error: no codonyat== pin found in {rel}")
        unique = set(matches)
        if len(unique) > 1:
            raise SystemExit(f"error: multiple codonyat pins in {rel}: {sorted(unique)}")
        pins[rel] = matches[0]
    if missing:
        raise SystemExit("error: pin file(s) not found: " + ", ".join(missing))
    return pins


def fetch_latest(url: str = PYPI_JSON) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "nf-codonyat-version-check"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SystemExit(f"error: failed to read PyPI metadata from {url}: {exc}") from exc
    version = (payload.get("info") or {}).get("version")
    if not version:
        raise SystemExit(f"error: PyPI JSON at {url} has no info.version")
    return str(version)


def emit_warning(message: str) -> None:
    print(f"::warning::{message}")


def write_summary(line: str) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(line.rstrip() + "\n")
    print(line)


def main() -> int:
    root = repo_root()
    pins = extract_pins(root)
    latest = fetch_latest()
    pin_versions = sorted(set(pins.values()))
    pin_desc = ", ".join(f"{path}={ver}" for path, ver in pins.items())

    if len(pin_versions) > 1:
        emit_warning(f"codonyat pins disagree ({pin_desc})")
        write_summary(f"codonyat pins disagree: {pin_desc}.")

    behind = [ver for ver in pin_versions if is_behind(ver, latest)]
    if behind:
        pinned = behind[0] if len(behind) == 1 else ", ".join(behind)
        message = f"Pinned codonyat {pinned} is behind PyPI latest {latest}"
        emit_warning(message)
        write_summary(f"{message} ({pin_desc}).")
        return 0

    pinned = pin_versions[0]
    write_summary(f"Pinned codonyat {pinned} matches the latest PyPI release ({pin_desc}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
