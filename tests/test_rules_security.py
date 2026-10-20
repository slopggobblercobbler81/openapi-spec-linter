"""Tests for security rules."""

import pytest
from openapi_spec_linter.loader import load_spec_from_string
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules.security_rules import (
    SecurityDefinedRule,
    SecuritySchemeExistsRule,
)


def test_security_defined_missing():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses: {200: {description: ok}}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = SecurityDefinedRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "No security requirements defined" in issues[0].message


def test_security_defined_present():
    raw = """
    openapi: 3.0.3
    security:
      - OAuth2: [read]
    paths:
      /users:
        get:
          responses: {200: {description: ok}}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = SecurityDefinedRule().check(ctx, cfg)
    assert len(issues) == 0


def test_security_scheme_exists_missing():
    raw = """
    openapi: 3.0.3
    security:
      - UnknownAuth: []
    paths:
      /users:
        get:
          security:
            - AnotherUnknown: []
          responses: {200: {description: ok}}
    components:
      securitySchemes:
        RealAuth:
          type: http
          scheme: bearer
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = SecuritySchemeExistsRule().check(ctx, cfg)
    assert len(issues) == 2
    messages = [i.message for i in issues]
    assert any("UnknownAuth" in m for m in messages)
    assert any("AnotherUnknown" in m for m in messages)
