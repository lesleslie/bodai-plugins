from __future__ import annotations

from typer.testing import CliRunner

from bodai_plugins.cli import app


def test_cli_help_lists_subcommands() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "validate" in result.stdout


def test_init_command_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "plugin_name" in result.stdout  # Typer 0.15+ renders positional args as {plugin_name}


def test_validate_command_accepts_fix_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "--fix" in result.stdout