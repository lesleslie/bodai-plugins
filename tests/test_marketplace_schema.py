from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

MARKETPLACE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "bodai-plugins marketplace manifest",
    "type": "object",
    "required": ["schema_version", "name", "owner", "plugins"],
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "name": {"type": "string", "pattern": r"^[a-z][a-z0-9-]*$"},
        "owner": {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "plugins": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "source"],
                "properties": {
                    "name": {"type": "string", "pattern": r"^[a-z][a-z0-9-]*$"},
                    "source": {"type": "string"},
                    "ref": {"type": "string"},
                },
            },
        },
    },
}


def test_marketplace_manifest_validates_against_schema() -> None:
    payload = json.loads(MANIFEST_PATH.read_text())
    jsonschema.validate(payload, MARKETPLACE_SCHEMA)


def test_marketplace_plugin_names_are_unique() -> None:
    payload = json.loads(MANIFEST_PATH.read_text())
    names = [p["name"] for p in payload["plugins"]]
    assert len(names) == len(set(names)), f"duplicate plugin names: {names}"
