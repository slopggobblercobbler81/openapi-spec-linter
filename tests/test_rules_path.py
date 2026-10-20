"""Tests for path and operation rules."""

import pytest
from openapi_spec_linter.loader import load_spec_from_string
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules.path_rules import (
    PathTrailingSlashRule,
    PathParametersMatchRule,
    OperationDescriptionRule,
    OperationSummaryRule,
    OperationTagsRule,
    OperationIdRule,
    OperationIdUniqueRule,
    OperationIdCasingRule,
)


def test_path_trailing_slash():
    raw = """
    openapi: 3.0.3
    paths:
      /:
        get: {responses: {200: {description: ok}}}
      /users/:
        get: {responses: {200: {description: ok}}}
      /items:
        get: {responses: {200: {description: ok}}}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = PathTrailingSlashRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "trailing slash" in issues[0].message
    assert issues[0].path == "/paths/~1users~1"
    assert issues[0].suggestion == "Rename '/users/' to '/users'."


def test_path_parameters_match():
    raw = """
    openapi: 3.0.3
    paths:
      /users/{id}:
        get:
          responses: {200: {description: ok}}
      /teams/{teamId}:
        parameters:
          - name: teamId
            in: path
            required: true
        get:
          parameters:
            - name: extraParam
              in: path
          responses: {200: {description: ok}}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = PathParametersMatchRule().check(ctx, cfg)

    # Issue 1: {id} has no matching parameter
    # Issue 2: extraParam is defined in: path but not in /teams/{teamId} template
    assert len(issues) == 2
    rule_ids = [i.rule_id for i in issues]
    assert all(r == "path-parameters-match" for r in rule_ids)


def test_operation_description_and_summary():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses: {200: {description: ok}}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()

    desc_issues = OperationDescriptionRule().check(ctx, cfg)
    assert len(desc_issues) == 1
    assert "missing a description" in desc_issues[0].message

    summary_issues = OperationSummaryRule().check(ctx, cfg)
    assert len(summary_issues) == 1
    assert "missing a summary" in summary_issues[0].message


def test_operation_tags():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          responses: {200: {description: ok}}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = OperationTagsRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "no tags defined" in issues[0].message


def test_operation_id_rules():
    raw = """
    openapi: 3.0.3
    paths:
      /users:
        get:
          operationId: "get-items"
          responses: {200: {description: ok}}
      /items:
        get:
          operationId: "get-items" # Duplicate
          responses: {200: {description: ok}}
      /other:
        get:
          operationId: "invalid name with spaces!"
          responses: {200: {description: ok}}
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()

    dup_issues = OperationIdUniqueRule().check(ctx, cfg)
    assert len(dup_issues) == 1
    assert "Duplicate operationId 'get-items'" in dup_issues[0].message

    casing_issues = OperationIdCasingRule().check(ctx, cfg)
    assert len(casing_issues) == 1
    assert "invalid characters or spaces" in casing_issues[0].message
