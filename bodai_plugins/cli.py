"""Typer CLI entry point for `bodai-plugins`."""

from __future__ import annotations

from pathlib import Path

import typer

from bodai_plugins import __version__

app = typer.Typer(
    name="bodai-plugins",
    help="Marketplace scaffold CLI for Bodai MCP-server Claude Code plugins.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"bodai-plugins {__version__}")
        raise typer.Exit(code=0)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Bodai plugins marketplace scaffold CLI."""


@app.command()
def init(
    plugin_name: str = typer.Argument(..., help="Plugin namespace (e.g. 'mahavishnu')."),
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Target directory for the scaffold.",
    ),
    url: str = typer.Option(
        "http://localhost:8680/mcp",
        "--url",
        help="MCP server URL to write to .mcp.json (default: mahavishnu port).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing plugin files.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Print each file as it is written.",
    ),
) -> None:
    """Scaffold a new plugin directory at PATH."""
    from bodai_plugins.scripts.init_bodai_plugin import scaffold_plugin

    plugin_dir = scaffold_plugin(
        name=plugin_name, target=path, url=url, force=force, verbose=verbose,
    )
    typer.echo(f"scaffolded plugin at {plugin_dir}")


@app.command()
def validate(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Plugin or marketplace directory to validate.",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Auto-fix issues where safe.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Print per-file diagnostic detail.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON.",
    ),
) -> None:
    """Validate a plugin or marketplace structure."""
    import json

    from bodai_plugins.scripts.validate_bodai_plugin import validate_plugin

    plugin_dir = path if (path / ".claude-plugin").is_dir() else None
    if plugin_dir is None:
        typer.echo(f"no plugin manifest found at {path}; pass --path pointing at a plugin directory")
        raise typer.Exit(code=2)

    issues = validate_plugin(plugin_dir, fix=fix)
    payload = {
        "plugin": str(plugin_dir),
        "issue_count": len(issues),
        "issues": [{"code": i.code, "message": i.message, "path": str(i.path)} for i in issues],
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
    else:
        if not issues:
            typer.echo(f"OK: {plugin_dir}")
            return
        typer.echo(f"{len(issues)} issue(s) in {plugin_dir}:", err=True)
        for issue in issues:
            typer.echo(f"  {issue.code}: {issue.message} ({issue.path})", err=True)
            if verbose:
                typer.echo(f"    at: {issue.path}", err=True)
        raise typer.Exit(code=1)


marketplace_app = typer.Typer(help="Manage the marketplace manifest.")
app.add_typer(marketplace_app, name="marketplace")


@marketplace_app.command("add")
def marketplace_add(
    name: str = typer.Option(..., "--name", help="Plugin name."),
    source: str = typer.Option(..., "--source", help="Path or URL to the plugin source."),
    ref: str = typer.Option("main", "--ref", help="Git ref to pin."),
    manifest: Path = typer.Option(
        Path(".claude-plugin/marketplace.json"),
        "--manifest",
        help="Path to the marketplace manifest.",
    ),
) -> None:
    """Register a plugin in the marketplace manifest."""
    from bodai_plugins.scripts.manage_marketplace import add_plugin_entry

    add_plugin_entry(manifest, name=name, source=source, ref=ref)
    typer.echo(f"added {name} -> {manifest}")


@marketplace_app.command("validate")
def marketplace_validate(
    manifest: Path = typer.Option(
        Path(".claude-plugin/marketplace.json"),
        "--manifest",
        help="Path to the marketplace manifest (default: ./marketplace.json).",
    ),
    cache: Path = typer.Option(
        Path.home() / ".claude" / "skills" / ".installer-cache.json",
        "--cache",
        help="Output installer cache path.",
    ),
    plugin_root: Path = typer.Option(
        Path("."),
        "--plugin-root",
        help="Root directory under which plugin sources are resolved.",
    ),
    commit_message: str | None = typer.Option(
        None,
        "--commit-message",
        help="If set, commit the marketplace manifest atomically after the cache write (P-10).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit JSON output instead of a human-readable summary.",
    ),
) -> None:
    """Walk every plugin's commands/skills/agents dirs and update the installer cache.

    Phase 5 plan §5 task #1, #5, #7. Atomicity per plan §10.7 P-10:

    - Filesystem write to ``cache`` is atomic (.tmp -> rename).
    - Concurrency guarded by ``fcntl`` lock on adjacent
      ``.installer-cache.lock`` (F-7).
    - When ``--commit-message`` is set, the marketplace manifest is
      git-committed atomically (no success without the commit).
    """
    from bodai_plugins.scripts.validate_marketplace import run_validate

    try:
        result = run_validate(
            manifest_path=manifest,
            cache_path=cache,
            plugin_root=plugin_root,
            commit_message=commit_message,
            workdir=manifest.parent,
        )
    except RuntimeError as exc:
        if json_output:
            import json as _json

            typer.echo(_json.dumps({"error": str(exc)}, indent=2))
        else:
            typer.echo(f"validate failed: {exc}", err=True)
        raise typer.Exit(code=1)

    if json_output:
        import json as _json

        typer.echo(_json.dumps(result, indent=2))
    else:
        typer.echo(
            f"validated {result['plugins']} plugin(s): "
            f"{result['skills']} skill(s), {result['agents']} agent(s)\n"
            f"  cache: {result['cache_path']}\n"
            f"  git_commit: {result['git_commit'] or '(none — not a git repo)'}"
        )


if __name__ == "__main__":
    app()
