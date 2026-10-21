import pytest
from openapi_spec_linter.rules.schema_rules import ParameterDescriptionRule
from openapi_spec_linter.models import LintContext
from openapi_spec_linter.config import LinterConfig

def test_deprecated_parameter_missing_description():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {
                            "name": "param1",
                            "in": "query",
                            "deprecated": True
                        }
                    ],
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    context = LintContext(file_path="test.yaml", raw_content="", spec=spec)
    rule = ParameterDescriptionRule()
    issues = rule.check(context, LinterConfig())
    assert len(issues) > 0
    assert any("description" in issue.message.lower() for issue in issues)
