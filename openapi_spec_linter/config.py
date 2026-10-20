"""Configuration management for openapi-spec-linter."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from .models import Severity


DEFAULT_CONFIG_FILENAME = ".openapi-linter.yaml"

DEFAULT_CONFIG_CONTENT = """# openapi-spec-linter configuration file
# Documentation & rules: https://github.com/slopggobblercobbler81/openapi-spec-linter

# Severity threshold to trigger a non-zero exit code: error | warning | info
fail_level: error

# File patterns to exclude from linting
ignore_files:
  - "**/node_modules/**"
  - "**/vendor/**"
  - "**/dist/**"

# Override rule severities: error | warning | info | off
rules:
  # Metadata & Information
  info-contact: warning
  info-description: error
  info-version: error
  info-license: info
  openapi-version: error

  # Paths & Operations
  path-no-trailing-slash: error
  path-parameters-match: error
  operation-tags: warning
  operation-summary: warning
  operation-description: warning
  operation-id: warning
  operation-id-unique: error
  operation-id-casing: info

  # Responses & Status Codes
  valid-status-code: error
  response-description: error
  success-response-present: error
  response-content-defined: warning
  error-response-present: warning

  # Components, Schemas & Refs
  no-dangling-refs: error
  no-unused-schemas: info
  param-description: warning
  schema-description: info

  # Security
  security-defined: info
  security-scheme-exists: error

# Custom rule options
options:
  # List of additional custom HTTP status codes to allow
  allowed_status_codes: []
"""


class LinterConfig:
    """Represents runtime linter configuration."""

    def __init__(
        self,
        fail_level: Severity = Severity.ERROR,
        rules: Optional[Dict[str, Severity]] = None,
        ignore_files: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        self.fail_level = fail_level
        self.rules: Dict[str, Severity] = rules or {}
        self.ignore_files: List[str] = ignore_files or []
        self.options: Dict[str, Any] = options or {}

    def get_rule_severity(self, rule_id: str, default: Severity) -> Severity:
        """Returns the effective severity for a rule."""
        if rule_id in self.rules:
            return self.rules[rule_id]
        return default

    def is_rule_enabled(self, rule_id: str, default: Severity) -> bool:
        """Checks if a rule is enabled (severity != OFF)."""
        sev = self.get_rule_severity(rule_id, default)
        return sev != Severity.OFF

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinterConfig":
        raw_fail = data.get("fail_level", "error")
        fail_level = Severity.from_str(raw_fail)

        rules: Dict[str, Severity] = {}
        raw_rules = data.get("rules", {})
        if isinstance(raw_rules, dict):
            for r_id, r_sev in raw_rules.items():
                if isinstance(r_sev, bool):
                    rules[r_id] = Severity.OFF if not r_sev else Severity.ERROR
                else:
                    rules[r_id] = Severity.from_str(str(r_sev))

        ignore_files = data.get("ignore_files", [])
        if not isinstance(ignore_files, list):
            ignore_files = []

        options = data.get("options", {})
        if not isinstance(options, dict):
            options = {}

        return cls(
            fail_level=fail_level,
            rules=rules,
            ignore_files=ignore_files,
            options=options,
        )

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "LinterConfig":
        """Load configuration from a specified file or default locations."""
        candidates = []
        if config_path:
            candidates.append(Path(config_path))
        else:
            candidates.extend(
                [
                    Path(DEFAULT_CONFIG_FILENAME),
                    Path(".openapi-linter.yml"),
                    Path("openapi-linter.yaml"),
                    Path("openapi-linter.yml"),
                ]
            )

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                try:
                    content = candidate.read_text(encoding="utf-8")
                    data = yaml.safe_load(content)
                    if isinstance(data, dict):
                        return cls.from_dict(data)
                except Exception:
                    pass

        return cls()


def create_default_config_file(target_path: Optional[str] = None) -> str:
    """Create a default configuration file."""
    path = Path(target_path or DEFAULT_CONFIG_FILENAME)
    path.write_text(DEFAULT_CONFIG_CONTENT, encoding="utf-8")
    return str(path)
