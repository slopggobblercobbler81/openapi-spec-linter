# 📑 openapi-spec-linter

[![CI](https://github.com/slopggobblercobbler81/openapi-spec-linter/actions/workflows/ci.yml/badge.svg)](https://github.com/slopggobblercobbler81/openapi-spec-linter/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> **Production-grade OpenAPI (Swagger) 3.0/3.1 specification linter, schema validator, and best-practices quality gate for CI/CD.**

---

## Features

- **Multi-Format Parsing**: Validate YAML and JSON OpenAPI v3.0.x and v3.1.x specifications.
- **Comprehensive Quality Rules**:
  - Enforce operation summaries, descriptions, and unique operation IDs.
  - Require explicit parameter schemas and valid status code declarations.
  - Validate security schemes, OAuth2 flows, and scopes.
  - Check polymorphic schema discriminators and circular references.
- **CI/CD Ready**: Exit code protocols, JSON summary output, and colored terminal reporting with line/column precision.

---

## Installation

```bash
pip install openapi-spec-linter
```
Or with [uv](https://github.com/astral-sh/uv):
```bash
uv pip install openapi-spec-linter
```

---

## Usage

```bash
# Lint an OpenAPI file
openapi-spec-linter lint openapi.yaml

# Lint with strict error thresholds and JSON output
openapi-spec-linter lint openapi.json --format json --strict

# Custom config file
openapi-spec-linter lint openapi.yaml --config .openapi-lint.yaml
```

---

## 🧭 Companion Tools & Ecosystem Cross-References

`openapi-spec-linter` is built to integrate cleanly with industry-standard API tooling:

- **Companion Upstream Linters:**
  - [`stoplightio/spectral`](https://github.com/stoplightio/spectral) — Flexible JSON/YAML linter for OpenAPI, AsyncAPI, and custom rule sets.
  - [`python-jsonschema/jsonschema`](https://github.com/python-jsonschema/jsonschema) — An implementation of the JSON Schema specification for Python.
- **Related Ecosystem Sibling Tools:**
  - [`api-contract-diff`](https://github.com/slopggobblercobbler81/api-contract-diff) — Detect breaking changes and semantic differences between OpenAPI versions.
  - [`schema-faker-cli`](https://github.com/slopggobblercobbler81/schema-faker-cli) — Generate realistic mock JSON payloads from OpenAPI specifications.
  - [`json-schema-diff`](https://github.com/slopggobblercobbler81/json-schema-diff) — Semantic breaking change detector for nested JSON schemas.

---

## License

This project is licensed under the [MIT License](LICENSE).
