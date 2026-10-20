"""Tests for response and status code rules."""

import pytest
from openapi_spec_linter.loader import load_spec_from_string
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules.response_rules import (
    ValidStatusCodeRule,
    ResponseDescriptionRule,
    SuccessResponsePresentRule,
    ResponseContentDefinedRule,
    ErrorResponsePresentRule,
)


def test_valid_status_code_rule():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses:
            "200": {description: ok}
            "209": {description: non-standard}
            "999": {description: invalid}
            "default": {description: fallback}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = ValidStatusCodeRule().check(ctx, cfg)
    assert len(issues) == 2
    codes = [i.message for i in issues]
    assert any("209" in m for m in codes)
    assert any("999" in m for m in codes)


def test_valid_status_code_allowed_options():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses:
            "209": {description: custom allowed}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig(options={"allowed_status_codes": ["209"]})
    issues = ValidStatusCodeRule().check(ctx, cfg)
    assert len(issues) == 0


def test_response_description_missing_or_empty():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses:
            "200": {}
            "404": {description: ""}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = ResponseDescriptionRule().check(ctx, cfg)
    assert len(issues) == 2
    assert all(i.rule_id == "response-description" for i in issues)


def test_success_response_present():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses:
            "404": {description: not found}
            "500": {description: server error}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = SuccessResponsePresentRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "does not define any 2xx success response" in issues[0].message


def test_response_content_defined():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses:
            "200":
              description: ok
              # missing content
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = ResponseContentDefinedRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "does not define a 'content' media type schema" in issues[0].message
