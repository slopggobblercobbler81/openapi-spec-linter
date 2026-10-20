"""Tests for YAML/JSON spec loader and line tracking."""

import pytest
from openapi_spec_linter.loader import load_spec, load_spec_from_string, LineTrackingLoader
from openapi_spec_linter.models import Severity


def test_load_nonexistent_file():
    context, result = load_spec("non_existent_file_path.yaml")
    assert context is None
    assert result.parse_error is not None
    assert result.error_count == 1
    assert result.issues[0].rule_id == "FILE_NOT_FOUND"


def test_load_malformed_yaml():
    raw = """
    openapi: 3.0.0
      invalid_indent: [
    """
    context, result = load_spec_from_string(raw)
    assert context is None
    assert result.parse_error is not None
    assert result.issues[0].rule_id == "PARSE_ERROR"


def test_load_empty_file():
    context, result = load_spec_from_string("")
    assert context is None
    assert "File is empty" in result.parse_error


def test_load_non_dict_root():
    context, result = load_spec_from_string("- item1\n- item2")
    assert context is None
    assert "Root element must be a dictionary" in result.parse_error


def test_load_valid_yaml(valid_yaml_path):
    context, result = load_spec(valid_yaml_path)
    assert context is not None
    assert result.parse_error is None
    assert result.spec_version == "3.0.3"
    assert context.spec["info"]["title"] == "Petstore API"

    # Verify line mapping
    assert "/info" in context.line_map
    assert "/paths" in context.line_map
    line, col = context.get_line_col("/info")
    assert line is not None and line > 0


def test_load_valid_json(valid_json_path):
    context, result = load_spec(valid_json_path)
    assert context is not None
    assert result.parse_error is None
    assert result.spec_version == "3.0.3"
    assert context.spec["info"]["title"] == "Petstore API JSON"


def test_pointer_prefix_fallback():
    raw = """
    openapi: 3.0.0
    info:
      title: Example
      version: 1.0.0
    """
    loader = LineTrackingLoader(raw)
    data, err = loader.parse()
    assert err is None
    from openapi_spec_linter.models import LintContext
    ctx = LintContext(file_path="test.yaml", raw_content=raw, spec=data, line_map=loader.line_map)
    # Even if specific subproperty isn't mapped, prefix /info should resolve
    line, col = ctx.get_line_col("/info/nested/missing")
    assert line is not None
