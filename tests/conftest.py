"""Shared test fixtures."""

from pathlib import Path
import pytest

from openapi_spec_linter.loader import load_spec, load_spec_from_string
from openapi_spec_linter.config import LinterConfig


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_yaml_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "valid_petstore.yaml")


@pytest.fixture
def valid_json_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "valid_petstore.json")


@pytest.fixture
def invalid_yaml_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "invalid_sample.yaml")


@pytest.fixture
def default_config() -> LinterConfig:
    return LinterConfig()
