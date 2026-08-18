"""X-Ray Cloud integration with typed payload mapping and explicit mutation control."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import requests

from core.config import Settings, get_settings
from domain.models import ExecutionResult, TestPlan
from infrastructure.security import ExecutionPolicy
from integrations.jira import IntegrationError


class XRayGateway(Protocol):
    def map_test_plan(self, plan: TestPlan) -> dict[str, Any]: ...

    def import_test_plan(self, plan: TestPlan, *, approved: bool) -> dict[str, Any]: ...

    def publish_execution(self, result: ExecutionResult, *, approved: bool) -> dict[str, Any]: ...


@dataclass
class XRayClient:
    settings: Settings | None = None
    session: requests.Session = field(default_factory=requests.Session)
    _token: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.settings = self.settings or get_settings()
        self.policy = ExecutionPolicy(self.settings)

    def map_test_plan(self, plan: TestPlan) -> dict[str, Any]:
        return {
            "tests": [
                {
                    "testType": {"name": _xray_test_type(case.test_type.value)},
                    "summary": case.title,
                    "description": case.objective,
                    "labels": list(dict.fromkeys(["qualtan", *case.tags])),
                    "steps": [
                        {
                            "action": step.action,
                            "result": step.expected_result,
                            "data": "\n".join(f"{item.key}={item.value}" for item in step.test_data),
                        }
                        for step in case.steps
                    ],
                }
                for case in plan.cases
            ]
        }

    def import_test_plan(self, plan: TestPlan, *, approved: bool) -> dict[str, Any]:
        self.policy.assert_mutation_allowed("xray.import_test_plan", approved)
        assert self.settings is not None
        self.settings.validate("xray")
        return self._post("/import/test/bulk", self.map_test_plan(plan))

    def publish_execution(self, result: ExecutionResult, *, approved: bool) -> dict[str, Any]:
        self.policy.assert_mutation_allowed("xray.publish_execution", approved)
        assert self.settings is not None
        self.settings.validate("xray")
        payload = {
            "info": {"summary": f"QUALTAN execution {result.run_id}", "description": result.stderr[-2000:]},
            "tests": [],
        }
        return self._post("/import/execution", payload)

    def _authenticate(self) -> str:
        if self._token:
            return self._token
        assert self.settings is not None
        response = self.session.post(
            f"{self.settings.xray_base_url.rstrip('/')}/authenticate",
            json={"client_id": self.settings.xray_client_id, "client_secret": self.settings.xray_client_secret},
            timeout=20,
        )
        try:
            response.raise_for_status()
            self._token = response.text.strip('"')
        except requests.RequestException as error:
            raise IntegrationError(f"X-Ray authentication failed: {error}") from error
        if not self._token:
            raise IntegrationError("X-Ray authentication returned an empty token.")
        return self._token

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        assert self.settings is not None
        response = self.session.post(
            f"{self.settings.xray_base_url.rstrip('/')}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {self._authenticate()}", "Content-Type": "application/json"},
            timeout=30,
        )
        try:
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as error:
            raise IntegrationError(f"X-Ray request to {path} failed: {error}") from error
        return body if isinstance(body, dict) else {"result": body}


@dataclass
class InMemoryXRayClient:
    imported_plans: list[dict[str, Any]] = field(default_factory=list)
    executions: list[dict[str, Any]] = field(default_factory=list)

    def map_test_plan(self, plan: TestPlan) -> dict[str, Any]:
        return XRayClient().map_test_plan(plan)

    def import_test_plan(self, plan: TestPlan, *, approved: bool) -> dict[str, Any]:
        if not approved:
            raise IntegrationError("Fixture X-Ray client still requires approval for mutation.")
        payload = self.map_test_plan(plan)
        self.imported_plans.append(payload)
        return {"imported": len(payload["tests"]), "mode": "in_memory"}

    def publish_execution(self, result: ExecutionResult, *, approved: bool) -> dict[str, Any]:
        if not approved:
            raise IntegrationError("Fixture X-Ray client still requires approval for mutation.")
        payload = {"run_id": result.run_id, "status": result.status.value}
        self.executions.append(payload)
        return {"published": True, "mode": "in_memory"}


def _xray_test_type(test_type: str) -> str:
    return {"web": "Manual", "api": "Generic", "graphql": "Generic", "security": "Generic", "performance": "Generic"}.get(test_type, "Manual")
""
