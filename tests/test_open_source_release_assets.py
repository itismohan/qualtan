from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_sbom_module():
    spec = importlib.util.spec_from_file_location("qualtan_generate_sbom", ROOT / "scripts" / "generate_sbom.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_release_assets_exist_and_document_governed_defaults() -> None:
    required = (
        "LICENSE",
        "NOTICE",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "DCO.txt",
        "GOVERNANCE.md",
        "MAINTAINERS.md",
        "SECURITY.md",
        "SUPPORT.md",
        "RELEASE.md",
        "CHANGELOG.md",
        "MANIFEST.in",
        "pyproject.toml",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/pull_request_template.md",
        "docs/OPEN_SOURCE_RELEASE.md",
        "examples/offline-demo/README.md",
    )
    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path

    security_policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "disabled by default" in security_policy
    assert "recorded approval" in security_policy
    assert "arbitrary shell" in security_policy


def test_package_metadata_exposes_supported_public_cli() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'name = "qualtan"' in pyproject
    assert 'requires-python = ">=3.11"' in pyproject
    assert 'qualtan = "cli.main:cli"' in pyproject
    assert 'license = "Apache-2.0"' in pyproject
    assert 'license-files = ["LICENSE", "NOTICE"]' in pyproject


def test_declared_dependency_sbom_is_cyclonedx_and_contains_python_and_node_components() -> None:
    sbom = _load_sbom_module().build_bom()

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["metadata"]["component"]["name"] == "qualtan"
    component_names = {component["name"] for component in sbom["components"]}
    assert "pydantic" in component_names
    assert "@playwright/test" in component_names
