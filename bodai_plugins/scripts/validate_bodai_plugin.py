"""Validate a Bodai MCP-server plugin structure."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: Path


REQUIRED_MANIFEST_KEYS = {"schema_version", "name", "version", "mcpServers"}
MIN_PLUGIN_VERSION = "1.0.0"


def _read_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _issue(code: str, message: str, path: Path) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, path=path)


def validate_plugin(plugin_dir: Path, *, fix: bool = False) -> list[ValidationIssue]:
    """Validate the plugin at ``plugin_dir``.

    When ``fix`` is True, safe auto-fixes are applied (writes a missing
    manifest stub, creates the ``commands/`` directory).
    """
    issues: list[ValidationIssue] = []
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    mcp_json_path = plugin_dir / ".mcp.json"
    commands_dir = plugin_dir / "commands"

    # 1. manifest must exist
    if not manifest_path.is_file():
        issues.append(_issue("MISSING_MANIFEST", "plugin.json is missing", manifest_path))
        if fix:
            (plugin_dir / ".claude-plugin").mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": MIN_PLUGIN_VERSION,
                        "name": plugin_dir.name,
                        "version": "0.1.0",
                        "mcpServers": ".mcp.json",
                    },
                    indent=2,
                )
                + "\n"
            )
            issues.clear()
            return validate_plugin(plugin_dir, fix=True)

    # 2. commands/ must exist
    if not commands_dir.is_dir():
        if fix:
            commands_dir.mkdir()
        else:
            issues.append(_issue("MISSING_COMMANDS_DIR", "commands/ directory is missing", commands_dir))

    # 3. mcp.json must exist
    if not mcp_json_path.is_file():
        if fix:
            mcp_json_path.write_text(json.dumps({plugin_dir.name: {"type": "http", "url": "x"}}, indent=2) + "\n")
        else:
            issues.append(_issue("MISSING_MCP_JSON", ".mcp.json is missing", mcp_json_path))

    data = _read_json(manifest_path)
    if isinstance(data, dict):
        # 4. required keys
        missing = REQUIRED_MANIFEST_KEYS - set(data.keys())
        if missing:
            issues.append(
                _issue(
                    "MISSING_MANIFEST_KEYS",
                    f"manifest missing keys: {sorted(missing)}",
                    manifest_path,
                )
            )

        # 5. name must equal directory basename
        declared_name = data.get("name")
        if declared_name and declared_name != plugin_dir.name:
            issues.append(
                _issue(
                    "NAME_MISMATCH",
                    f"manifest name {declared_name!r} != directory name {plugin_dir.name!r}",
                    manifest_path,
                )
            )

        # 6. mcpServers file path must exist
        mcp_servers = data.get("mcpServers")
        if isinstance(mcp_servers, str) and not (plugin_dir / mcp_servers).is_file():
            issues.append(
                _issue(
                    "MISSING_MCP_SERVERS_FILE",
                    f"mcpServers path {mcp_servers!r} does not exist",
                    plugin_dir / mcp_servers,
                )
            )

    return issues
