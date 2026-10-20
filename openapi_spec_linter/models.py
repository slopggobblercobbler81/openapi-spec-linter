"""Data models and enums for openapi-spec-linter."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Severity(str, Enum):
    """Rule severity level."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    OFF = "off"

    @classmethod
    def from_str(cls, val: str) -> "Severity":
        val_lower = str(val).strip().lower()
        for member in cls:
            if member.value == val_lower:
                return member
        if val_lower in ("warn", "warning"):
            return cls.WARNING
        if val_lower in ("err", "error"):
            return cls.ERROR
        if val_lower in ("information", "info"):
            return cls.INFO
        if val_lower in ("none", "disabled", "off", "ignore"):
            return cls.OFF
        raise ValueError(f"Unknown severity level: {val}")


@dataclass
class LintIssue:
    """Represents a single rule violation in an OpenAPI specification."""
    rule_id: str
    message: str
    severity: Severity
    path: str  # JSON Pointer like '/paths/~1users/get'
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion,
        }


@dataclass
class LintResult:
    """Result of linting a single specification file."""
    file_path: str
    issues: List[LintIssue] = field(default_factory=list)
    spec_version: Optional[str] = None
    parse_error: Optional[str] = None

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def infos(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == Severity.INFO]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def info_count(self) -> int:
        return len(self.infos)

    @property
    def total_count(self) -> int:
        return len(self.issues)

    def is_clean(self, fail_level: Severity = Severity.ERROR) -> bool:
        """Return True if there are no issues at or above fail_level."""
        if fail_level == Severity.ERROR:
            return self.error_count == 0
        if fail_level == Severity.WARNING:
            return self.error_count == 0 and self.warning_count == 0
        if fail_level == Severity.INFO:
            return self.total_count == 0
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "spec_version": self.spec_version,
            "parse_error": self.parse_error,
            "counts": {
                "errors": self.error_count,
                "warnings": self.warning_count,
                "infos": self.info_count,
                "total": self.total_count,
            },
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class LintContext:
    """Context passed to rules during inspection."""
    file_path: str
    raw_content: str
    spec: Dict[str, Any]
    line_map: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    def get_line_col(self, pointer: str) -> Tuple[Optional[int], Optional[int]]:
        """Lookup approximate (line, column) for a given JSON pointer."""
        if pointer in self.line_map:
            return self.line_map[pointer]
        
        # Try progressively shorter prefix pointers
        parts = pointer.strip("/").split("/")
        while parts:
            prefix = "/" + "/".join(parts)
            if prefix in self.line_map:
                return self.line_map[prefix]
            parts.pop()

        return None, None
