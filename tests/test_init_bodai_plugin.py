from __future__ import annotations

from pathlib import Path

from bodai_plugins.scripts.init_bodai_plugin import scaffold_plugin


def test_scaffold_creates_plugin_manifest(tmp_path: Path) -> None:
    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path)
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    assert manifest.is_file()
    import json

    data = json.loads(manifest.read_text())
    assert data["name"] == "mahavishnu"
    assert data["version"] == "0.1.0"
    assert "mcpServers" in data


def test_scaffold_creates_commands_directory(tmp_path: Path) -> None:
    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path)
    assert (plugin_dir / "commands").is_dir()


def test_scaffold_creates_mcp_json(tmp_path: Path) -> None:
    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path)
    mcp_json = plugin_dir / ".mcp.json"
    assert mcp_json.is_file()


def test_scaffold_refuses_overwrite_without_force(tmp_path: Path) -> None:
    scaffold_plugin(name="mahavishnu", target=tmp_path)
    import pytest

    with pytest.raises(FileExistsError):
        scaffold_plugin(name="mahavishnu", target=tmp_path, force=False)


def test_scaffold_overwrites_with_force(tmp_path: Path) -> None:
    scaffold_plugin(name="mahavishnu", target=tmp_path)
    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path, force=True)
    assert plugin_dir.is_dir()


def test_scaffold_rejects_empty_name(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError):
        scaffold_plugin(name="", target=tmp_path)


def test_scaffold_rejects_dot_name(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError):
        scaffold_plugin(name=".", target=tmp_path)


def test_scaffold_rejects_double_dot_name(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError):
        scaffold_plugin(name="..", target=tmp_path)


def test_scaffold_rejects_absolute_name(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError):
        scaffold_plugin(name="/tmp/evil", target=tmp_path)


def test_scaffold_rejects_name_with_slash(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError):
        scaffold_plugin(name="foo/bar", target=tmp_path)


def test_scaffold_rejects_name_with_backslash(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError):
        scaffold_plugin(name="foo\\bar", target=tmp_path)
