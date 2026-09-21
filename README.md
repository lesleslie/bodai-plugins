# bodai-plugins

Marketplace scaffolding CLI for the core [Bodai ecosystem](https://github.com/lesleslie/bodai) Claude Code plugins.

## Scope

This marketplace distributes plugins for the **core bodai components only**: mahavishnu, session-buddy, crackerjack, akosha, and oneiric. WWW MCP integration servers (`*-mcp`) live in the [www-mcp-servers marketplace](https://github.com/lesleslie/www-mcp-servers).

When adding a new plugin, ask: is this part of the core bodai control plane? If yes, add it here. If it's an independent integration server, it belongs in `www-mcp-servers`.

## Install

```bash
uv tool install bodai-plugins
```

## Use

```bash
# Scaffold a new plugin in the current repo
bodai-plugins init mahavishnu

# Validate the plugin structure
bodai-plugins validate --verbose

# Auto-fix issues
bodai-plugins validate --fix
```

## Add the marketplace to Claude Code

```bash
claude plugin marketplace add https://github.com/lesleslie/bodai-plugins
```

## Plugins distributed

See `.claude-plugin/marketplace.json` for the canonical list.
```
