#!/usr/bin/env python3
"""Generate a minimal CycloneDX SBOM from QUALTAN dependency declarations.

This script intentionally reads declared Python requirements and the committed Node
lockfile rather than environment-specific installed packages. The generated SBOM
is deterministic for a given repository revision and does not read credentials.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _python_components(requirements_path: Path) -> list[dict[str, str]]:
    components: list[dict[str, str]] = []
    pattern = re.compile(r"^([A-Za-z0-9_.-]+)\s*(.*)$")
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        name, constraints = match.groups()
        components.append(
            {
                "type": "library",
                "name": name,
                "version": constraints.strip() or "unspecified",
                "purl": f"pkg:pypi/{name.lower()}",
                "properties": [{"name": "qualtan:declared-constraint", "value": constraints.strip() or "unspecified"}],
            }
        )
    return components


def _node_components(lockfile_path: Path) -> list[dict[str, str]]:
    lockfile = json.loads(lockfile_path.read_text(encoding="utf-8"))
    packages = lockfile.get("packages", {})
    components: list[dict[str, str]] = []
    for package_path, details in sorted(packages.items()):
        if not package_path or not package_path.startswith("node_modules/"):
            continue
        name = details.get("name") or package_path.removeprefix("node_modules/")
        version = details.get("version", "unspecified")
        components.append(
            {
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:npm/{name}@{version}",
            }
        )
    return components


def build_bom() -> dict[str, Any]:
    components = _python_components(ROOT / "requirements.txt")
    lockfile = ROOT / "package-lock.json"
    if lockfile.is_file():
        components.extend(_node_components(lockfile))
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:qualtan-declared-dependencies",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "qualtan",
                "version": "0.1.0",
                "licenses": [{"license": {"id": "Apache-2.0"}}],
            },
            "tools": [{"vendor": "QUALTAN Contributors", "name": "generate_sbom.py"}],
        },
        "components": components,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a declared-dependency CycloneDX SBOM.")
    parser.add_argument("--output", type=Path, required=True, help="Destination JSON path.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_bom(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
