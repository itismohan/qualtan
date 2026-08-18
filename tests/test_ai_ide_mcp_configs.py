from __future__ import annotations

import json
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_json(relative_path: str) -> dict:
    return json.loads((PROJECT_ROOT / relative_path).read_text(encoding="utf-8"))


def test_cursor_and_claude_project_mcp_configs_define_a_local_stdio_qualtan_server() -> None:
    cursor = _load_json(".cursor/mcp.json")["mcpServers"]["qualtan"]
    claude = _load_json(".mcp.json")["mcpServers"]["qualtan"]

    assert cursor["type"] == "stdio"
    assert cursor["command"] == "python"
    assert cursor["args"] == ["${workspaceFolder}/mcp_server.py"]
    assert cursor["env"]["PYTHONPATH"] == "${workspaceFolder}"

    assert claude["type"] == "stdio"
    assert claude["command"] == "python"
    assert claude["args"] == ["${CLAUDE_PROJECT_DIR:-.}/mcp_server.py"]
    assert claude["env"]["PYTHONPATH"] == "${CLAUDE_PROJECT_DIR:-.}"


def test_codex_project_config_uses_local_stdio_and_prompts_for_tool_approval() -> None:
    payload = tomllib.loads((PROJECT_ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    server = payload["mcp_servers"]["qualtan"]

    assert server["command"] == "python"
    assert server["args"] == ["mcp_server.py"]
    assert server["cwd"] == "."
    assert server["default_tools_approval_mode"] == "prompt"
    assert server["tool_timeout_sec"] >= 60


def test_kiro_workspace_config_keeps_tools_reviewable_and_does_not_autoapprove() -> None:
    server = _load_json(".kiro/settings/mcp.json")["mcpServers"]["qualtan"]

    assert server["command"] == "python"
    assert server["args"] == ["mcp_server.py"]
    assert server["disabled"] is False
    assert server["autoApprove"] == []
    assert server["disabledTools"] == []


def test_project_mcp_templates_do_not_embed_machine_specific_paths_or_credentials() -> None:
    template_paths = [
        ".cursor/mcp.json",
        ".mcp.json",
        ".codex/config.toml",
        ".kiro/settings/mcp.json",
    ]
    combined = "\n".join((PROJECT_ROOT / path).read_text(encoding="utf-8") for path in template_paths).lower()

    assert "/users/" not in combined
    assert "authorization" not in combined
    assert "api_key" not in combined
    assert "secret" not in combined
