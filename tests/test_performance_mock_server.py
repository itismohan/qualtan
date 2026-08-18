from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from typing import Iterator
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from performance.mock_api_server import create_mock_api_server


@contextmanager
def mock_server() -> Iterator[str]:
    server = create_mock_api_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _read_json(request: Request) -> tuple[int, dict]:
    with urlopen(request, timeout=3) as response:  # noqa: S310 -- local mock URL only
        return response.status, json.loads(response.read())


def test_mock_rest_endpoint_requires_expected_authorization_and_returns_fixture() -> None:
    with mock_server() as base_url:
        status, payload = _read_json(Request(f"{base_url}/api/v1/resource", headers={"Authorization": "Bearer token"}))
        assert status == 200
        assert payload == {"id": "resource-1", "name": "Mocked performance resource", "status": "ready"}

        unauthorized = Request(f"{base_url}/api/v1/resource")
        try:
            _read_json(unauthorized)
        except HTTPError as error:
            assert error.code == 401
        else:
            raise AssertionError("Expected the mock endpoint to reject a missing authorization header.")


def test_mock_graphql_endpoint_returns_fixture_and_validates_query_shape() -> None:
    with mock_server() as base_url:
        request = Request(
            f"{base_url}/graphql",
            data=json.dumps({"query": "query { user(id: \"1\") { id username email } }"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        status, payload = _read_json(request)
        assert status == 200
        assert payload["data"]["user"] == {"id": "1", "username": "mocked-user", "email": "mocked-user@example.test"}

        unsupported = Request(
            f"{base_url}/graphql",
            data=json.dumps({"query": "query { products { id } }"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        status, payload = _read_json(unsupported)
        assert status == 200
        assert payload["data"] is None
        assert payload["errors"][0]["extensions"]["code"] == "BAD_QUERY"
