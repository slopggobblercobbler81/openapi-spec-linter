"""Tests for info and metadata rules."""

import pytest
from openapi_spec_linter.loader import load_spec_from_string
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules.info_rules import (
    OpenAPIVersionRule,
    InfoContactRule,
    InfoDescriptionRule,
    InfoVersionRule,
    InfoLicenseRule,
)


def test_openapi_version_valid():
    raw = "openapi: '3.0.3'\ninfo: {title: Test, version: 1.0.0, description: Valid description}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = OpenAPIVersionRule().check(ctx, cfg)
    assert len(issues) == 0


def test_openapi_version_swagger_warning():
    raw = "swagger: '2.0'\ninfo: {title: Test, version: 1.0.0, description: Valid description}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = OpenAPIVersionRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "Swagger '2.0'" in issues[0].message


def test_openapi_version_invalid_format():
    raw = "openapi: '4.0.0'\ninfo: {title: Test, version: 1.0.0}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = OpenAPIVersionRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "Unsupported OpenAPI version" in issues[0].message


def test_info_description_missing():
    raw = "openapi: '3.0.3'\ninfo: {title: Test, version: 1.0.0}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = InfoDescriptionRule().check(ctx, cfg)
    assert len(issues) == 1
    assert issues[0].rule_id == "info-description"


def test_info_description_too_short():
    raw = "openapi: '3.0.3'\ninfo: {title: Test, version: 1.0.0, description: 'Hi'}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = InfoDescriptionRule().check(ctx, cfg)
    assert len(issues) == 1
    assert "too short" in issues[0].message


def test_info_contact_missing_or_empty():
    raw = "openapi: '3.0.3'\ninfo: {title: Test, version: 1.0.0, description: 'Valid API description'}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = InfoContactRule().check(ctx, cfg)
    assert len(issues) == 1
    assert issues[0].rule_id == "info-contact"

    # Contact with empty fields
    raw2 = "openapi: '3.0.3'\ninfo: {title: Test, version: 1.0.0, description: 'Valid API description', contact: {}}"
    ctx2, _ = load_spec_from_string(raw2)
    issues2 = InfoContactRule().check(ctx2, cfg)
    assert len(issues2) == 1


def test_info_version_missing():
    raw = "openapi: '3.0.3'\ninfo: {title: Test, description: 'Valid API description'}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = InfoVersionRule().check(ctx, cfg)
    assert len(issues) == 1
    assert issues[0].rule_id == "info-version"


def test_info_license_missing():
    raw = "openapi: '3.0.3'\ninfo: {title: Test, version: 1.0.0, description: 'Valid API description'}"
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = InfoLicenseRule().check(ctx, cfg)
    assert len(issues) == 1
    assert issues[0].rule_id == "info-license"
