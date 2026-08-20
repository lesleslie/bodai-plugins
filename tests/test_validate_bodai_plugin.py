from __future__ import annotations

import json
from pathlib import Path

from bodai_plugins.scripts.validate_bodai_plugin import (
    ValidationIssue,
    validate_plugin,
)


def test_validate_passes_on_valid_plugin(tmp_path: Path) -> None:
    plugin = tmp_path / "mahavishnu"
    plugin.mkdir()
    (plugin / ".claude-plugin").mkdir()
    (plugin / "commands").mkdir()
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "name": "mahavishnu",
                "version": "0.1.0",
                "mcpServers": ".mcp.json",
            }
        )
    )
    (plugin / ".mcp.json").write_text(json.dumps({"mahavishnu": {"type": "http", "url": "x"}}))

    issues = validate_plugin(plugin)
    assert issues == []


def test_validate_detects_missing_manifest(tmp_path: Path) -> None:
    plugin = tmp_path / "mahavishnu"
    plugin.mkdir()
    issues = validate_plugin(plugin)
    assert any(i.code == "MISSING_MANIFEST" for i in issues)


def test_validate_allows_short_name_when_dir_basename_differs(tmp_path: Path) -> None:
    # Regression: NAME_MISMATCH used to block -mcp repos whose manifest
    # kept the short form (graphics, css) while the directory kept the
    # long form (graphics-mcp, css-mcp). The directory basename is NOT
    # part of the "one string, three places" rule.
    plugin = tmp_path / "graphics-mcp"
    plugin.mkdir()
    (plugin / ".claude-plugin").mkdir()
    (plugin / "commands").mkdir()
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "name": "graphics",
                "version": "0.1.0",
                "mcpServers": ".mcp.json",
            }
        )
    )
    (plugin / ".mcp.json").write_text(json.dumps({"graphics": {"type": "http", "url": "x"}}))

    issues = validate_plugin(plugin)
    assert issues == []


def test_validate_detects_name_mcp_json_mismatch(tmp_path: Path) -> None:
    # Replaces the old NAME_MISMATCH (directory-name) check. The new rule
    # is: manifest.name must equal a top-level key in .mcp.json.
    plugin = tmp_path / "mahavishnu"
    plugin.mkdir()
    (plugin / ".claude-plugin").mkdir()
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "name": "vishnu",
                "version": "0.1.0",
                "mcpServers": ".mcp.json",
            }
        )
    )
    (plugin / ".mcp.json").write_text(json.dumps({"mahavishnu": {"type": "http", "url": "x"}}))

    issues = validate_plugin(plugin)
    assert any(i.code == "NAME_MCP_JSON_MISMATCH" for i in issues)


def test_validate_passes_when_name_in_multi_key_mcp_json(tmp_path: Path) -> None:
    # Aggregator plugins (e.g. mahavishnu's top-level .mcp.json) may list
    # many servers; manifest.name just needs to be one of them.
    plugin = tmp_path / "mahavishnu"
    plugin.mkdir()
    (plugin / ".claude-plugin").mkdir()
    (plugin / "commands").mkdir()
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "name": "mahavishnu",
                "version": "0.1.0",
                "mcpServers": ".mcp.json",
            }
        )
    )
    (plugin / ".mcp.json").write_text(
        json.dumps(
            {
                "akosha": {"type": "http", "url": "x"},
                "mahavishnu": {"type": "http", "url": "y"},
                "session-buddy": {"type": "http", "url": "z"},
            }
        )
    )

    issues = validate_plugin(plugin)
    assert issues == []


def test_validate_fix_writes_missing_manifest(tmp_path: Path) -> None:
    plugin = tmp_path / "mahavishnu"
    plugin.mkdir()
    fixed = validate_plugin(plugin, fix=True)
    assert (plugin / ".claude-plugin" / "plugin.json").is_file()
    assert fixed == []


def test_validation_issue_dataclass() -> None:
    issue = ValidationIssue(code="X", message="y", path=Path("/z"))
    assert issue.code == "X"
    assert issue.message == "y"
    assert issue.path == Path("/z")