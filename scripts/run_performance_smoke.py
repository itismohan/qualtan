"""Run the Locust scenario against QUALTAN's ephemeral local mock API.

The runner never resolves or contacts external API hosts. It exists to verify that
the committed Locust scenario can exercise its REST and GraphQL request paths.
"""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# The script executes from the repository root, so the local package is importable.
sys.path.insert(0, str(PROJECT_ROOT))

from performance.mock_api_server import create_mock_api_server  # noqa: E402


def main() -> int:
    server = create_mock_api_server()
    server_thread = threading.Thread(target=server.serve_forever, name="qualtan-mock-api", daemon=True)
    server_thread.start()
    host, port = server.server_address[:2]
    mock_url = f"http://{host}:{port}"

    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        "performance/locustfile.py",
        "--headless",
        "-u",
        "2",
        "-r",
        "2",
        "-t",
        "6s",
        "--host",
        mock_url,
        "--only-summary",
    ]
    try:
        result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
        return result.returncode
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
