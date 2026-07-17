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

    plugin_dir = scaffold_plugin(name=plugin_name, target=path, force=force, verbose=verbose)
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


if __name__ == "__main__":
    app()
