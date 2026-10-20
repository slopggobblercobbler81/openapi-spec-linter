"""Tests for configuration file loading and options."""

import pytest
from pathlib import Path
from openapi_spec_linter.config import LinterConfig, create_default_config_file
from openapi_spec_linter.models import Severity


def test_default_config():
    config = LinterConfig()
    assert config.fail_level == Severity.ERROR
    assert config.is_rule_enabled("path-no-trailing-slash", Severity.ERROR)
    assert config.get_rule_severity("path-no-trailing-slash", Severity.ERROR) == Severity.ERROR


def test_config_from_dict():
    data = {
        "fail_level": "warning",
        "rules": {
            "path-no-trailing-slash": "off",
            "info-contact": "error",
            "operation-tags": False,
        },
        "ignore_files": ["**/tests/**"],
        "options": {
            "allowed_status_codes": [209],
        },
    }
    cfg = LinterConfig.from_dict(data)
    assert cfg.fail_level == Severity.WARNING
    assert not cfg.is_rule_enabled("path-no-trailing-slash", Severity.ERROR)
    assert not cfg.is_rule_enabled("operation-tags", Severity.WARNING)
    assert cfg.get_rule_severity("info-contact", Severity.WARNING) == Severity.ERROR
    assert cfg.options["allowed_status_codes"] == [209]
    assert "**/tests/**" in cfg.ignore_files


def test_create_and_load_default_config(tmp_path):
    target = tmp_path / "custom-linter.yaml"
    created = create_default_config_file(str(target))
    assert Path(created).exists()

    loaded = LinterConfig.load(str(target))
    assert loaded.fail_level == Severity.ERROR
    assert loaded.get_rule_severity("path-no-trailing-slash", Severity.WARNING) == Severity.ERROR
