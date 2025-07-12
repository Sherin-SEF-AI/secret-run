"""Tests for CLI functionality."""

import pytest
from typer.testing import CliRunner

from secret_run.cli.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_version_command(runner):
    """Test the version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "secret-run version" in result.stdout


def test_help_command(runner):
    """Test the help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "secret-run" in result.stdout
    assert "Secure command execution" in result.stdout


def test_doctor_command(runner):
    """Test the doctor command."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code in [0, 1]  # May have warnings
    assert "Running system health check" in result.stdout


def test_info_command(runner):
    """Test the info command."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "System Information" in result.stdout


def test_run_command_help(runner):
    """Test the run command help."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Execute commands with secrets" in result.stdout


def test_validate_command_help(runner):
    """Test the validate command help."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate secrets and configurations" in result.stdout


def test_config_command_help(runner):
    """Test the config command help."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "Manage configuration" in result.stdout


def test_audit_command_help(runner):
    """Test the audit command help."""
    result = runner.invoke(app, ["audit", "--help"])
    assert result.exit_code == 0
    assert "Audit and monitoring commands" in result.stdout 