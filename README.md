# openapi-spec-linter

[![CI](https://github.com/slopggobblercobbler81/openapi-spec-linter/actions/workflows/ci.yml/badge.svg)](https://github.com/slopggobblercobbler81/openapi-spec-linter/actions)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-pep8-green.svg)](https://pep8.org/)

Production-grade OpenAPI v3 (YAML/JSON) specification linter and quality gate for modern API teams, CI/CD pipelines, and SDK generators.

---

## Highlights

- **Complete OpenAPI v3.0 & v3.1 Support**: Seamlessly lints both YAML (`.yaml`, `.yml`) and JSON (`.json`) specifications.
- **Accurate Source Line Mapping**: Identifies exact line and column coordinates for every warning and error using AST position mapping.
- **18+ Battle-Tested Rules**: Covers API metadata, path semantics, HTTP status codes, schema validity, dangling refs, unused models, and security requirements.
- **Configurable Severity & Overrides**: Tailor rules (`error`, `warning`, `info`, `off`) per project using `.openapi-linter.yaml` or command-line options.
- **Rich Multi-Format Reporting**:
  - **Terminal**: Colorized, formatted tables powered by Rich.
  - **JSON**: Machine-readable output for custom toolchains.
  - **Markdown**: Formatted reports for GitHub PR comments and wikis.
  - **JUnit XML**: Direct test-report integration for Jenkins, GitLab CI, CircleCI, and GitHub Actions.
- **CI Quality Gate Ready**: Predictable exit codes (`0` = clean/allowed warnings, `1` = lint violations exceeding threshold, `2` = file read or YAML/JSON syntax errors).

---

## Installation

Install from source or via pip:

```bash
pip install openapi-spec-linter
```

For development:

```bash
git clone https://github.com/slopggobblercobbler81/openapi-spec-linter.git
cd openapi-spec-linter
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Lint an OpenAPI specification
```bash
openapi-spec-linter lint openapi.yaml
```

### 2. Lint multiple specs or directories recursively
```bash
openapi-spec-linter lint specs/
```

### 3. List all built-in rules
```bash
openapi-spec-linter rules
```

### 4. Initialize a project configuration file
```bash
openapi-spec-linter init
```
This generates a starter `.openapi-linter.yaml` in your current working directory.

---

## CLI Reference

### `openapi-spec-linter lint [OPTIONS] [FILES]...`

Lints one or more OpenAPI spec files or directories.

| Option | Shorthand | Default | Description |
|---|---|---|---|
| `--format` | `-f` | `terminal` | Output format: `terminal`, `text`, `json`, `markdown`, `junit`. |
| `--config` | `-c` | `None` | Path to custom YAML configuration file. |
| `--fail-level` | | `error` | Minimum severity triggering exit code 1 (`error`, `warning`, `info`). |
| `--ignore-rule` | | `None` | Rule ID to disable (repeatable). |
| `--output` | `-o` | `None` | Write report output to file instead of stdout. |
| `--recursive / --no-recursive` | `-r / -R` | `True` | Recursively scan directories for `.yaml`, `.yml`, and `.json`. |
| `--color / --no-color` | | `True` | Enable or disable terminal ANSI colors. |
| `--help` | `-h` | | Show help message and exit. |

#### Examples

**Export Markdown report for GitHub PR:**
```bash
openapi-spec-linter lint spec.yaml --format markdown -o lint-report.md
```

**Generate JUnit XML for CI test reporting:**
```bash
openapi-spec-linter lint ./specs --format junit -o test-results.xml
```

**Fail on warnings as well as errors:**
```bash
openapi-spec-linter lint spec.yaml --fail-level warning
```

**Ignore specific rules on the fly:**
```bash
openapi-spec-linter lint spec.yaml --ignore-rule operation-tags --ignore-rule schema-description
```

---

### `openapi-spec-linter rules [OPTIONS]`

Lists all registered linting rules.

| Option | Description |
|---|---|
| `--json` | Output rules as structured JSON array. |

---

### `openapi-spec-linter init [OPTIONS]`

Generates a default `.openapi-linter.yaml` configuration file.

| Option | Shorthand | Description |
|---|---|---|
| `--output` | `-o` | Custom target configuration file path. |

---

## Built-In Rules Catalog

| Rule ID | Category | Default Severity | Description |
|---|---|---|---|
| `openapi-version` | `info` | **ERROR** | Specification must declare a valid OpenAPI 3.0.x or 3.1.x version. |
| `info-version` | `info` | **ERROR** | `info.version` field must be defined and non-empty. |
| `info-description` | `info` | **ERROR** | `info.description` must be provided and contain meaningful text. |
| `info-contact` | `info` | **WARNING** | `info.contact` should provide name, email, or URL for maintainers. |
| `info-license` | `info` | **INFO** | `info.license` should define API license name. |
| `path-no-trailing-slash` | `paths` | **ERROR** | API endpoint paths must not end with a trailing slash (`/`). |
| `path-parameters-match` | `paths` | **ERROR** | Path template variables (e.g. `{id}`) must match `in: path` parameter definitions. |
| `operation-description` | `paths` | **WARNING** | Operations must define a non-empty `description`. |
| `operation-summary` | `paths` | **WARNING** | Operations should define a short `summary`. |
| `operation-tags` | `paths` | **WARNING** | Operations should be categorized with at least one tag. |
| `operation-id` | `paths` | **WARNING** | Operations should specify an `operationId` for SDK generators. |
| `operation-id-unique` | `paths` | **ERROR** | Every `operationId` must be globally unique across the spec. |
| `operation-id-casing` | `paths` | **INFO** | `operationId` should use alphanumeric characters, underscores, or hyphens. |
| `valid-status-code` | `responses` | **ERROR** | Response keys must be standard IANA HTTP status codes, wildcards (`2XX`), or `default`. |
| `response-description` | `responses` | **ERROR** | Every response object must define a non-empty `description`. |
| `success-response-present` | `responses` | **ERROR** | Operations must define at least one `2xx` or `2XX` success response. |
| `response-content-defined` | `responses` | **WARNING** | Successful responses returning data should define a `content` media type schema. |
| `error-response-present` | `responses` | **INFO** | Operations should define 4xx/5xx or `default` error responses. |
| `no-dangling-refs` | `schemas` | **ERROR** | Local JSON references (`$ref: '#/...'`) must resolve to valid spec definitions. |
| `no-unused-schemas` | `schemas` | **INFO** | Component schemas should be referenced elsewhere in the document. |
| `param-description` | `schemas` | **WARNING** | All parameters should provide a descriptive explanation. |
| `schema-description` | `schemas` | **INFO** | Component schemas should provide model descriptions. |
| `security-defined` | `security` | **INFO** | API should specify authentication/security requirements. |
| `security-scheme-exists` | `security` | **ERROR** | Schemes used in `security` must exist in `components.securitySchemes`. |

---

## Configuration (`.openapi-linter.yaml`)

Customize severity levels, ignore rules, or exclude files:

```yaml
# Minimum severity that causes exit code 1 (error, warning, info)
fail_level: error

# File ignore patterns (glob patterns)
ignore_files:
  - "**/legacy/**"
  - "*_draft.yaml"

# Rule severity overrides (error, warning, info, off)
rules:
  # Elevate warning to error
  operation-tags: error
  info-contact: error

  # Demote error to warning
  info-description: warning

  # Disable specific rules
  operation-id-casing: off
  no-unused-schemas: off
```

---

## Python API Usage

You can also integrate `openapi-spec-linter` directly into your Python scripts and test pipelines:

```python
from openapi_spec_linter.loader import load_spec
from openapi_spec_linter.config import LinterConfig
from openapi_spec_linter.rules import RuleRegistry
from openapi_spec_linter.reporter import TerminalReporter

# 1. Load specification
context, result = load_spec("api/v1/openapi.yaml")
if result.parse_error:
    print(f"Failed to parse spec: {result.parse_error}")
    exit(1)

# 2. Run rules engine
config = LinterConfig.load()
issues = RuleRegistry.run_all(context, config)
result.issues.extend(issues)

# 3. Format output
reporter = TerminalReporter(color=True)
print(reporter.report([result]))

# 4. Check status
if not result.is_clean(config.fail_level):
    exit(1)
```

---

## CI/CD Integration

### GitHub Actions Workflow

Add this step to `.github/workflows/api-lint.yml`:

```yaml
name: OpenAPI Spec Lint

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install linter
        run: pip install openapi-spec-linter

      - name: Lint API Specs
        run: openapi-spec-linter lint openapi.yaml --fail-level error
```

---

## Testing

Run tests and coverage reports locally using `pytest`:

```bash
pytest --cov=openapi_spec_linter --cov-report=term-missing
```

---

## License

This project is licensed under the [MIT License](LICENSE).
