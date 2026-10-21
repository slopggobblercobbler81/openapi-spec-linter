import pytest
from openapi_spec_linter.rules.path_rules import OperationIdUniqueRule
from openapi_spec_linter.rules.base import LintContext, LinterConfig, Severity

def test_operation_id_uniqueness_duplicate():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "responses": {"200": {"description": "OK"}}
                }
            },
            "/admin/users": {
                "get": {
                    "operationId": "getUsers",
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    context = LintContext(file_path="openapi.yaml", raw_content="", spec=spec)
    config = LinterConfig()
    rule = OperationIdUniqueRule()
    issues = rule.check(context, config)
    assert len(issues) == 1
    assert "Duplicate operationId 'getUsers'" in issues[0].message

def test_operation_id_uniqueness_unique():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "responses": {"200": {"description": "OK"}}
                }
            },
            "/admin/users": {
                "get": {
                    "operationId": "getAdminUsers",
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    context = LintContext(file_path="openapi.yaml", raw_content="", spec=spec)
    config = LinterConfig()
    rule = OperationIdUniqueRule()
    issues = rule.check(context, config)
    assert len(issues) == 0
