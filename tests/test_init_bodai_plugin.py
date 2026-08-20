from __future__ import annotations

import json
from pathlib import Path

from bodai_plugins.scripts.init_bodai_plugin import scaffold_plugin


def test_scaffold_creates_plugin_manifest(tmp_path: Path) -> None:
    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path)
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    assert manifest.is_file()
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


def test_scaffold_writes_mdformat_toml(tmp_path: Path) -> None:
    """``.mdformat.toml`` must exclude commands/*.md so mdformat runs don't
    corrupt the YAML frontmatter that slash commands depend on."""
    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path)
    mdformat_toml = plugin_dir / ".mdformat.toml"
    assert mdformat_toml.is_file()
    content = mdformat_toml.read_text()
    assert 'exclude = ["commands/*.md"]' in content


def test_scaffold_default_url(tmp_path: Path) -> None:
    """Default URL is the historical mahavishnu port (8680)."""
    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path)
    mcp_data = json.loads((plugin_dir / ".mcp.json").read_text())
    assert mcp_data["mahavishnu"]["url"] == "http://localhost:8680/mcp"


def test_scaffold_url_is_configurable(tmp_path: Path) -> None:
    """``url`` keyword overrides the default and is written to .mcp.json."""
    plugin_dir = scaffold_plugin(
        name="css", target=tmp_path, url="http://localhost:3050/mcp",
    )
    mcp_data = json.loads((plugin_dir / ".mcp.json").read_text())
    assert mcp_data["css"]["url"] == "http://localhost:3050/mcp"


def test_scaffold_output_passes_validator(tmp_path: Path) -> None:
    """Round-trip: the scaffold output must satisfy validate_plugin()."""
    from bodai_plugins.scripts.validate_bodai_plugin import validate_plugin

    plugin_dir = scaffold_plugin(name="mahavishnu", target=tmp_path)
    issues = validate_plugin(plugin_dir)
    assert issues == [], f"scaffold output failed validation: {[i.code for i in issues]}"


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


def test_scaffold_rejects_name_with_control_characters(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError, match="control characters"):
        scaffold_plugin(name="\x00evil", target=tmp_path)
