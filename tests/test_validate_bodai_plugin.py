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


def test_validate_detects_name_mismatch(tmp_path: Path) -> None:
    plugin = tmp_path / "mahavishnu"
    plugin.mkdir()
    (plugin / ".claude-plugin").mkdir()
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "vishnu", "version": "0.1.0", "mcpServers": ".mcp.json"})
    )
    issues = validate_plugin(plugin)
    assert any(i.code == "NAME_MISMATCH" for i in issues)


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
