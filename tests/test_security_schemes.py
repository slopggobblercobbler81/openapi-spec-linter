import pytest
from openapi_spec_linter.loader import load_spec_from_string
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules.security_rules import (
    SecuritySchemeExistsRule,
)

def test_oauth2_flows_validation():
    raw = """
    openapi: 3.0.3
    security:
      - OAuth2Flows: [read]
    paths:
      /data:
        get:
          responses: {200: {description: ok}}
    components:
      securitySchemes:
        OAuth2Flows:
          type: oauth2
          flows:
            authorizationCode:
              authorizationUrl: https://example.com/oauth/authorize
              tokenUrl: https://example.com/oauth/token
              scopes:
                read: Read access
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = SecuritySchemeExistsRule().check(ctx, cfg)
    assert len(issues) == 0

def test_bearer_jwt_security_scheme():
    raw = """
    openapi: 3.0.3
    security:
      - BearerJWT: []
    paths:
      /protected:
        get:
          responses: {200: {description: ok}}
    components:
      securitySchemes:
        BearerJWT:
          type: http
          scheme: bearer
          bearerFormat: JWT
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = SecuritySchemeExistsRule().check(ctx, cfg)
    assert len(issues) == 0
