"""Tests for schemas, $ref, and parameters."""

import pytest
from openapi_spec_linter.loader import load_spec_from_string
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules.schema_rules import (
    NoDanglingRefsRule,
    NoUnusedSchemasRule,
    ParameterDescriptionRule,
    SchemaDescriptionRule,
)


def test_no_dangling_refs():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses:
            "200":
              description: ok
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/NonExistentUser"
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = NoDanglingRefsRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "Unresolved local reference '#/components/schemas/NonExistentUser'" in issues[0].message


def test_no_unused_schemas():
    raw = """
    openapi: 3.0.3
    components:
      schemas:
        UsedSchema:
          type: object
        UnusedSchema:
          type: object
    paths:
      /users:
        get:
          responses:
            "200":
              description: ok
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/UsedSchema"
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = NoUnusedSchemasRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "UnusedSchema" in issues[0].message


def test_parameter_description():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          parameters:
            - name: queryParam
              in: query
              # missing description
          responses:
            "200": {description: ok}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = ParameterDescriptionRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "Parameter 'queryParam' is missing a description" in issues[0].message


def test_schema_description():
    raw = """
    openapi: 3.0.3
    components:
      schemas:
        User:
          type: object
          # missing description
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = SchemaDescriptionRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "User' has no description" in issues[0].message
