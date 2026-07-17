from __future__ import annotations

import json
from pathlib import Path


from bodai_plugins.scripts.manage_marketplace import (
    add_plugin_entry,
    load_marketplace,
    render_marketplace,
)


def test_render_marketplace_returns_required_keys() -> None:
    payload = render_marketplace(name="bodai-plugins", owner="lesleslie", plugins=[])
    assert payload["name"] == "bodai-plugins"
    assert payload["owner"]["name"] == "lesleslie"
    assert payload["plugins"] == []
    assert "schema_version" in payload


def test_add_plugin_entry_appends(tmp_path: Path) -> None:
    manifest = tmp_path / "marketplace.json"
    manifest.write_text(json.dumps(render_marketplace(name="bodai-plugins", owner="lesleslie", plugins=[])))
    add_plugin_entry(
        manifest,
        name="mahavishnu",
        source="../mahavishnu",
        ref="main",
    )
    data = load_marketplace(manifest)
    assert len(data["plugins"]) == 1
    assert data["plugins"][0]["name"] == "mahavishnu"
    assert data["plugins"][0]["source"] == "../mahavishnu"


def test_add_plugin_entry_rejects_duplicate(tmp_path: Path) -> None:
    manifest = tmp_path / "marketplace.json"
    manifest.write_text(json.dumps(render_marketplace(name="bodai-plugins", owner="lesleslie", plugins=[])))
    add_plugin_entry(manifest, name="mahavishnu", source="../mahavishnu")
    import pytest

    with pytest.raises(ValueError):
        add_plugin_entry(manifest, name="mahavishnu", source="../elsewhere")
