"""Scaffold a Bodai MCP-server plugin directory."""

from __future__ import annotations

import json
from pathlib import Path

PLUGIN_MANIFEST_SCHEMA_VERSION = "1.0.0"
INITIAL_VERSION = "0.1.0"


def validate_plugin_name(name: str) -> None:
    """Validate a plugin name for use as both a manifest identifier and path component.

    The plugin name must equal the MCP server key and the slash-command namespace
    prefix (three places, one string). Reject any input that could split those
    three or escape the requested ``target`` directory.

    Raises ValueError if ``name`` is empty, reserved (``.`` or ``..``), an
    absolute path, or contains a path separator (``/`` or ``\\``).
    """
    if not name:
        raise ValueError("plugin name must not be empty")
    if name in (".", ".."):
        raise ValueError(f"plugin name {name!r} is reserved (current-directory or parent)")
    if Path(name).is_absolute():
        raise ValueError(f"plugin name {name!r} must not be an absolute path")
    if "/" in name or "\\" in name:
        raise ValueError(f"plugin name {name!r} must not contain path separators")
    if any(ord(c) < 0x20 or c == "\x7f" for c in name):
        raise ValueError(f"plugin name {name!r} must not contain control characters")


def _render_plugin_json(name: str) -> str:
    """Render `.claude-plugin/plugin.json` for a Bodai MCP-server plugin."""
    payload = {
        "schema_version": PLUGIN_MANIFEST_SCHEMA_VERSION,
        "name": name,
        "version": INITIAL_VERSION,
        "description": f"Bodai plugin for the {name} MCP server.",
        "author": {"name": "Bodai"},
        "keywords": ["bodai", "mcp", name],
        "mcpServers": ".mcp.json",
    }
    return json.dumps(payload, indent=2) + "\n"


def _render_mcp_json(name: str) -> str:
    """Render `.mcp.json` that wires the plugin's MCP server entry."""
    payload = {
        name: {
            "type": "http",
            "url": "http://localhost:8680/mcp",
            "description": f"{name} MCP server (update URL to match this server).",
        }
    }
    return json.dumps(payload, indent=2) + "\n"


def _render_readme(name: str) -> str:
    return (
        f"# {name} plugin\n\n"
        f"Bodai plugin for the `{name}` MCP server.\n\n"
        f"## Install\n\n"
        f"Add the `bodai-plugins` marketplace, then install this plugin:\n\n"
        f"```bash\n"
        f"claude plugin install {name}\n"
        f"```\n\n"
        f"## Commands\n\n"
        f"See `commands/`.\n"
    )


def scaffold_plugin(
    name: str,
    target: Path,
    *,
    force: bool = False,
    verbose: bool = False,
) -> Path:
    """Scaffold a plugin directory at ``target/<name>/``.

    Returns the plugin directory path.
    Raises FileExistsError if the directory exists and ``force`` is False.
    """
    validate_plugin_name(name)
    plugin_dir = target / name
    if plugin_dir.exists() and not force:
        raise FileExistsError(f"{plugin_dir} already exists; pass force=True to overwrite")

    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "commands").mkdir(exist_ok=True)
    (plugin_dir / ".claude-plugin").mkdir(exist_ok=True)

    files = {
        plugin_dir / ".claude-plugin" / "plugin.json": _render_plugin_json(name),
        plugin_dir / ".mcp.json": _render_mcp_json(name),
        plugin_dir / "README.md": _render_readme(name),
    }
    for path, content in files.items():
        path.write_text(content)
        if verbose:
            print(f"wrote {path}")

    return plugin_dir
