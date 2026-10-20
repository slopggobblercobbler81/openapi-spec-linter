"""Tests for OpenAPI 3.1 discriminator mapping validation."""

import pytest
from openapi_spec_linter.loader import load_spec_from_string
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules.schema_rules import NoDanglingRefsRule


def test_openapi_31_discriminator_mapping_valid():
    raw = """
    openapi: 3.1.0
    info:
      title: Test API
      version: 1.0.0
    paths:
      /pets:
        get:
          responses:
            "200":
              description: Success
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/Pet"
    components:
      schemas:
        Pet:
          type: object
          required:
            - petType
          properties:
            petType:
              type: string
          discriminator:
            propertyName: petType
            mapping:
              cat: "#/components/schemas/Cat"
              dog: "#/components/schemas/Dog"
        Cat:
          type: object
          allOf:
            - $ref: "#/components/schemas/Pet"
        Dog:
          type: object
          allOf:
            - $ref: "#/components/schemas/Pet"
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = NoDanglingRefsRule().check(ctx, cfg)
    assert len(issues) == 0


def test_openapi_31_discriminator_mapping_referenced():
    raw = """
    openapi: 3.1.0
    info:
      title: Test API
      version: 1.0.0
    paths:
      /pets:
        get:
          responses:
            "200":
              description: Success
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/Pet"
    components:
      schemas:
        Pet:
          type: object
          required:
            - petType
          properties:
            petType:
              type: string
          discriminator:
            propertyName: petType
            mapping:
              cat: "#/components/schemas/Cat"
        Cat:
          type: object
    """
    ctx, _ = load_spec_from_string(raw)
    cfg = LinterConfig()
    issues = NoDanglingRefsRule().check(ctx, cfg)
    assert len(issues) == 0
