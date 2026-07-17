# bodai-plugins

Marketplace scaffolding CLI for the [Bodai ecosystem](https://github.com/lesleslie/bodai) Claude Code plugins.

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