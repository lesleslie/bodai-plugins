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
    typer.echo(f"init: not yet implemented (would scaffold {plugin_name} at {path})")


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
    typer.echo(f"validate: not yet implemented (would validate {path})")


if __name__ == "__main__":
    app()