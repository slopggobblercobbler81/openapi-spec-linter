"""openapi-spec-linter: Production-grade OpenAPI v3 specification linter."""

__version__ = "1.0.0"

from .models import LintIssue, LintResult, Severity
from .loader import load_spec
from .config import LinterConfig
from .rules.base import RuleRegistry

__all__ = [
    "__version__",
    "LintIssue",
    "LintResult",
    "Severity",
    "load_spec",
    "LinterConfig",
    "RuleRegistry",
]
