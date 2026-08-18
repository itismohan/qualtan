"""Deterministic validation gates for generated QUALTAN artifacts."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from domain.models import GeneratedArtifact, QualityWorkItem, ValidationResult
from infrastructure.security import content_hash


class ValidationGate(Protocol):
    name: str

    def validate(self, work_item: QualityWorkItem) -> ValidationResult: ...


@dataclass(frozen=True, slots=True)
class SchemaIntegrityGate:
    name: str = "schema_integrity"

    def validate(self, work_item: QualityWorkItem) -> ValidationResult:
        failures: list[str] = []
        for artifact in work_item.artifacts:
            try:
                GeneratedArtifact.model_validate(artifact.model_dump(mode="json"))
            except Exception as error:
                failures.append(f"Artifact {artifact.artifact_id} violates its domain schema: {error}")
            for file in artifact.files:
                if file.content_hash != content_hash(file.content):
                    failures.append(f"{file.path}: content hash does not match file content.")
        return ValidationResult(
            validator=self.name,
            passed=not failures,
            summary="All generated artifacts satisfy strict domain contracts." if not failures else "Schema integrity validation failed.",
            details=failures,
        )


@dataclass(frozen=True, slots=True)
class TestCoverageGate:
    name: str = "acceptance_criteria_coverage"

    def validate(self, work_item: QualityWorkItem) -> ValidationResult:
        if work_item.test_plan is None:
            return ValidationResult(validator=self.name, passed=False, summary="No test plan exists for coverage evaluation.")
        expected = {criterion.criterion_id for criterion in work_item.story.acceptance_criteria}
        covered = {criterion for case in work_item.test_plan.cases for criterion in case.covered_criteria}
        missing = sorted(expected - covered)
        duplicate_ids = _duplicates([case.case_id for case in work_item.test_plan.cases])
        details = [f"Missing coverage for {criterion}." for criterion in missing]
        details.extend(f"Duplicate test-case ID: {case_id}." for case_id in duplicate_ids)
        return ValidationResult(
            validator=self.name,
            passed=not details,
            summary="Every acceptance criterion is covered by at least one unique test case." if not details else "Test-plan coverage gap detected.",
            details=details,
        )


@dataclass(frozen=True, slots=True)
class SourceSafetyGate:
    name: str = "generated_test_source_safety"

    _FORBIDDEN_PATTERNS = {
        "fixed sleep": "waitForTimeout(",
        "XPath locator": "xpath=",
        "dynamic evaluation": "eval(",
        "process execution": "child_process",
        "shell execution": "exec(",
        "hard-coded credential-like text": "password=",
    }

    def validate(self, work_item: QualityWorkItem) -> ValidationResult:
        details: list[str] = []
        files = [file for artifact in work_item.artifacts for file in artifact.files]
        if not files:
            details.append("No generated files exist.")
        for file in files:
            if not file.path.startswith("generated-tests/") or ".." in file.path.split("/"):
                details.append(f"{file.path}: unsafe generated file path.")
            if not file.path.endswith(".ts"):
                details.append(f"{file.path}: generated Playwright files must be TypeScript.")
            for description, pattern in self._FORBIDDEN_PATTERNS.items():
                if pattern.lower() in file.content.lower():
                    details.append(f"{file.path}: forbidden {description} pattern '{pattern}'.")
            if "@playwright/test" not in file.content:
                details.append(f"{file.path}: does not import @playwright/test.")
            if "expect(" not in file.content:
                details.append(f"{file.path}: contains no explicit assertion.")
        return ValidationResult(
            validator=self.name,
            passed=not details,
            summary="Generated source follows QUALTAN safety and maintainability rules." if not details else "Generated source violated safety or test-quality policy.",
            details=details,
        )


@dataclass(frozen=True, slots=True)
class TypeScriptCompileGate:
    project_root: Path
    timeout_seconds: int = 30
    name: str = "typescript_compile"

    def validate(self, work_item: QualityWorkItem) -> ValidationResult:
        started = time.perf_counter()
        files = [file for artifact in work_item.artifacts for file in artifact.files if file.path.endswith(".ts")]
        if not files:
            return ValidationResult(validator=self.name, passed=False, summary="No TypeScript artifacts are available for compilation.")
        if not shutil.which("npx"):
            return ValidationResult(validator=self.name, passed=False, summary="npx is required for the TypeScript compilation gate but is unavailable.")
        try:
            with tempfile.TemporaryDirectory(prefix="qualtan-compile-") as temp_dir:
                root = Path(temp_dir)
                generated_paths: list[str] = []
                for file in files:
                    destination = root / file.path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(file.content, encoding="utf-8")
                    generated_paths.append(str(destination))
                result = subprocess.run(
                    [
                        "npx",
                        "tsc",
                        "--noEmit",
                        "--skipLibCheck",
                        "--target",
                        "ES2020",
                        "--moduleResolution",
                        "node",
                        "--module",
                        "commonjs",
                        *generated_paths,
                    ],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(validator=self.name, passed=False, summary="TypeScript compilation exceeded the configured timeout.")
        except OSError as error:
            return ValidationResult(validator=self.name, passed=False, summary=f"Unable to launch TypeScript compiler: {error}")
        details = _output_lines(result.stdout, result.stderr)
        return ValidationResult(
            validator=self.name,
            passed=result.returncode == 0,
            summary="Generated TypeScript compiles successfully." if result.returncode == 0 else "Generated TypeScript failed compilation.",
            details=details,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )


@dataclass
class ValidationPipeline:
    gates: list[ValidationGate]

    def validate(self, work_item: QualityWorkItem) -> list[ValidationResult]:
        return [gate.validate(work_item) for gate in self.gates]


def default_validation_pipeline(project_root: str | Path) -> ValidationPipeline:
    return ValidationPipeline(
        gates=[
            SchemaIntegrityGate(),
            TestCoverageGate(),
            SourceSafetyGate(),
            TypeScriptCompileGate(project_root=Path(project_root)),
        ]
    )


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _output_lines(stdout: str, stderr: str, maximum: int = 30) -> list[str]:
    lines = [line for line in (stdout + "\n" + stderr).splitlines() if line.strip()]
    return lines[:maximum]
""
