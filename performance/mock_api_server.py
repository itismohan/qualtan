"""Local REST and GraphQL test server used by offline performance smoke checks."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class MockApiHandler(BaseHTTPRequestHandler):
    server_version = "QUALTANMockAPI/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/api/v1/resource":
            self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        if self.headers.get("Authorization") != "Bearer token":
            self._respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        self._respond(
            HTTPStatus.OK,
            {"id": "resource-1", "name": "Mocked performance resource", "status": "ready"},
        )

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/graphql":
            self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._respond(HTTPStatus.BAD_REQUEST, {"errors": [{"message": "Invalid JSON request"}]})
            return
        if "user" not in str(payload.get("query", "")):
            self._respond(
                HTTPStatus.OK,
                {"data": None, "errors": [{"message": "Unsupported mock query", "extensions": {"code": "BAD_QUERY"}}]},
            )
            return
        self._respond(
            HTTPStatus.OK,
            {"data": {"user": {"id": "1", "username": "mocked-user", "email": "mocked-user@example.test"}}},
        )

    def _respond(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args: object) -> None:
        """Keep smoke-test output focused on Locust's result summary."""


def create_mock_api_server(host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    """Create a server; port zero selects an available local port for parallel-safe tests."""

    return ThreadingHTTPServer((host, port), MockApiHandler)
