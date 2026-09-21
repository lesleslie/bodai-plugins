# Changelog

All notable changes to bodai-plugins will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Migrated the 18 WWW `*-mcp` plugins out of this marketplace to the new [www-mcp-servers marketplace](https://github.com/lesleslie/www-mcp-servers). The `*-mcp` integration servers are independent packages, not core bodai components, so they belong in the catalog that maintains them.
- Removed `dhara` from this marketplace. Dhara is no longer a bodai-core component and is now a standalone entity managed outside this plugin registry.
- Added `oneiric` back to this marketplace. Oneiric's FastMCP server has been re-introduced (14 tools, default port 8681) and is part of the core bodai control plane alongside mahavishnu, session-buddy, crackerjack, and akosha.
- Documented the "core bodai components only" scope in the README. Future `*-mcp` plugins go in `www-mcp-servers`; only control-plane bodai components belong here.

## [1.0.1] - 2026-07-16

### Fixed
- Trailing newlines in 7 bootstrap files (pyproject.toml, .gitignore, README.md, CHANGELOG.md, LICENSE, bodai_plugins/__init__.py, tests/test_cli.py).
- Removed placeholder-free f-strings in `bodai_plugins/scripts/init_bodai_plugin.py` (Ruff F541 compliance).

## [1.0.0] - 2026-07-16

### Added
- `bodai-plugins init <name>` scaffold command — creates plugin directory with `.claude-plugin/plugin.json`, `.mcp.json`, `commands/` dir, and a starter `README.md`. Supports `--force`, `--verbose`, `--path`.
- `bodai-plugins validate` command — checks plugin structure against the manifest schema; supports `--fix` for safe auto-repair, `--verbose` and `--json` output modes.
- `bodai-plugins marketplace add --name X --source Y --ref Z` command — registers plugins in the marketplace manifest; rejects duplicates.
- `scripts/audit_workflow_lifecycle.py` in mahavishnu — CI guard test for paired workflow decisions (in companion repo).
- CI guard test for the marketplace manifest (`tests/test_marketplace_schema.py`).
- 5 plugins registered in the initial marketplace: `mahavishnu`, `session-buddy`, `crackerjack`, `akosha`, `dhara`.

## [0.1.0] - 2026-07-16

### Added
- Initial marketplace repo skeleton with pyproject.toml, .gitignore, README, CHANGELOG, and MIT LICENSE.
- Placeholder for the `bodai-plugins` Typer-based scaffold CLI (added in subsequent releases).
