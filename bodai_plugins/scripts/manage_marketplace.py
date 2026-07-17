"""Read and write the bodai-plugins marketplace manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

MARKETPLACE_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class PluginEntry:
    name: str
    source: str
    ref: str = "main"

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "source": self.source, "ref": self.ref}


def render_marketplace(*, name: str, owner: str, plugins: list[PluginEntry]) -> dict[str, object]:
    return {
        "schema_version": MARKETPLACE_SCHEMA_VERSION,
        "name": name,
        "owner": {"name": owner},
        "plugins": [p.to_dict() for p in plugins],
    }


def load_marketplace(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def add_plugin_entry(
    manifest_path: Path,
    *,
    name: str,
    source: str,
    ref: str = "main",
) -> None:
    data = load_marketplace(manifest_path)
    plugins = list(data.get("plugins", []))
    if any(isinstance(p, dict) and p.get("name") == name for p in plugins):
        raise ValueError(f"plugin {name!r} already present in {manifest_path}")
    plugins.append(PluginEntry(name=name, source=source, ref=ref).to_dict())
    data["plugins"] = plugins
    manifest_path.write_text(json.dumps(data, indent=2) + "\n")
