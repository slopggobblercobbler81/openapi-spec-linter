"""Tests for Click CLI commands."""

import json
from pathlib import Path
from click.testing import CliRunner
from openapi_spec_linter.cli import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "openapi-spec-linter" in result.output


def test_cli_rules_table():
    runner = CliRunner()
    result = runner.invoke(cli, ["rules"])
    assert result.exit_code == 0
    assert "path-no-trailing-slash" in result.output
    assert "valid-status-code" in result.output


def test_cli_rules_json():
    runner = CliRunner()
    result = runner.invoke(cli, ["rules", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    rule_ids = [r["id"] for r in data]
    assert "path-no-trailing-slash" in rule_ids
    assert "info-description" in rule_ids


def test_cli_init(tmp_path):
    runner = CliRunner()
    target_config = tmp_path / "custom.yaml"
    result = runner.invoke(cli, ["init", "--output", str(target_config)])
    assert result.exit_code == 0
    assert target_config.exists()
    assert "fail_level" in target_config.read_text(encoding="utf-8")


def test_cli_lint_valid_yaml(valid_yaml_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", valid_yaml_path])
    assert result.exit_code == 0
    assert "No issues found" in result.output or "PASS" in result.output


def test_cli_lint_valid_json(valid_json_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", valid_json_path])
    assert result.exit_code == 0


def test_cli_lint_invalid_yaml(invalid_yaml_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", invalid_yaml_path])
    assert result.exit_code == 1
    assert "path-no-trailing-slash" in result.output or "valid-status-code" in result.output


def test_cli_lint_formats(invalid_yaml_path, tmp_path):
    runner = CliRunner()

    # JSON format
    json_out = runner.invoke(cli, ["lint", invalid_yaml_path, "--format", "json"])
    assert json_out.exit_code == 1
    parsed_json = json.loads(json_out.output)
    assert parsed_json["summary"]["total_errors"] > 0

    # Markdown format
    md_out = runner.invoke(cli, ["lint", invalid_yaml_path, "--format", "markdown"])
    assert md_out.exit_code == 1
    assert "# OpenAPI Lint Report" in md_out.output

    # JUnit format
    junit_out = runner.invoke(cli, ["lint", invalid_yaml_path, "--format", "junit"])
    assert junit_out.exit_code == 1
    assert "<testsuites" in junit_out.output

    # Output file
    out_file = tmp_path / "report.json"
    file_out = runner.invoke(cli, ["lint", invalid_yaml_path, "--format", "json", "--output", str(out_file)])
    assert file_out.exit_code == 1
    assert out_file.exists()


def test_cli_lint_nonexistent_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", "does_not_exist.yaml"])
    assert result.exit_code == 2
