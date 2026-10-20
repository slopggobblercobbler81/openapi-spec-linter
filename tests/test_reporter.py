"""Tests for result reporters."""

import json
from openapi_spec_linter.models import LintIssue, LintResult, Severity
from openapi_spec_linter.reporter import (
    TerminalReporter,
    JsonReporter,
    MarkdownReporter,
    JUnitReporter,
)


def _make_dummy_result():
    res = LintResult(file_path="api.yaml", spec_version="3.0.3")
    res.issues.append(
        LintIssue(
            rule_id="path-no-trailing-slash",
            message="Path ends with slash",
            severity=Severity.ERROR,
            path="/paths/~1users~1",
            line=12,
            column=4,
            suggestion="Rename to /users",
        )
    )
    res.issues.append(
        LintIssue(
            rule_id="operation-tags",
            message="Missing tags",
            severity=Severity.WARNING,
            path="/paths/~1users/get",
            line=15,
            column=6,
        )
    )
    return res


def test_terminal_reporter():
    res = _make_dummy_result()
    reporter = TerminalReporter(color=False)
    out = reporter.report([res])
    assert "File:" in out or "api.yaml" in out
    assert "path-no-trailing-slash" in out
    assert "Missing tags" in out


def test_json_reporter():
    res = _make_dummy_result()
    reporter = JsonReporter()
    out = reporter.report([res])
    data = json.loads(out)
    assert data["summary"]["total_errors"] == 1
    assert data["summary"]["total_warnings"] == 1
    assert len(data["files"]) == 1
    assert data["files"][0]["file_path"] == "api.yaml"
    assert data["files"][0]["issues"][0]["rule_id"] == "path-no-trailing-slash"


def test_markdown_reporter():
    res = _make_dummy_result()
    reporter = MarkdownReporter()
    out = reporter.report([res])
    assert "# OpenAPI Lint Report" in out
    assert "| Location | Severity | Rule ID | Message | Path |" in out
    assert "path-no-trailing-slash" in out


def test_junit_reporter():
    res = _make_dummy_result()
    reporter = JUnitReporter()
    out = reporter.report([res])
    assert '<?xml version="1.0" encoding="UTF-8"?>' in out
    assert '<testsuites name="openapi-spec-linter"' in out
    assert '<error message="Path ends with slash"' in out
    assert '<failure message="Missing tags"' in out
