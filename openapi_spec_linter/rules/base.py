"""Base rule definitions and registry."""

import abc
import re
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Type

from ..models import LintContext, LintIssue, Severity
from ..config import LinterConfig


HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


class BaseRule(abc.ABC):
    """Abstract base class for all OpenAPI linting rules."""

    id: str = ""
    name: str = ""
    description: str = ""
    category: str = "general"
    default_severity: Severity = Severity.WARNING

    @abc.abstractmethod
    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        """Execute rule check and return any found issues."""
        raise NotImplementedError

    def create_issue(
        self,
        message: str,
        path: str,
        context: LintContext,
        config: LinterConfig,
        suggestion: Optional[str] = None,
    ) -> LintIssue:
        """Helper to create a LintIssue with correct severity and line info."""
        severity = config.get_rule_severity(self.id, self.default_severity)
        line, col = context.get_line_col(path)
        return LintIssue(
            rule_id=self.id,
            message=message,
            severity=severity,
            path=path,
            line=line,
            column=col,
            suggestion=suggestion,
        )


def iter_operations(
    spec: Dict[str, Any]
) -> Generator[Tuple[str, str, Dict[str, Any], str], None, None]:
    """
    Yields (path, method, operation_dict, pointer) for each operation in spec.
    """
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return

    for path_key, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        # Escape path_key for pointer
        escaped_path = path_key.replace("~", "~0").replace("/", "~1")
        for method, op in path_item.items():
            if method.lower() in HTTP_METHODS and isinstance(op, dict):
                pointer = f"/paths/{escaped_path}/{method.lower()}"
                yield path_key, method.lower(), op, pointer


def resolve_local_ref(spec: Dict[str, Any], ref: str) -> Tuple[Optional[Any], bool]:
    """
    Resolves an internal JSON reference (e.g. '#/components/schemas/User').
    Returns (resolved_obj, exists_bool).
    """
    if not ref.startswith("#/"):
        return None, False

    tokens = ref[2:].split("/")
    curr: Any = spec
    for raw_token in tokens:
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(curr, dict) and token in curr:
            curr = curr[token]
        elif isinstance(curr, list) and token.isdigit() and int(token) < len(curr):
            curr = curr[int(token)]
        else:
            return None, False
    return curr, True


def collect_refs(obj: Any) -> Set[str]:
    """Recursively collects all $ref values in a data structure."""
    refs: Set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                refs.add(v)
            else:
                refs.update(collect_refs(v))
    elif isinstance(obj, list):
        for item in obj:
            refs.update(collect_refs(item))
    return refs


class RuleRegistry:
    """Registry holding all known lint rules."""

    _rules: Dict[str, Type[BaseRule]] = {}

    @classmethod
    def register(cls, rule_cls: Type[BaseRule]) -> Type[BaseRule]:
        if not rule_cls.id:
            raise ValueError(f"Rule class {rule_cls.__name__} has no 'id' defined")
        cls._rules[rule_cls.id] = rule_cls
        return rule_cls

    @classmethod
    def get(cls, rule_id: str) -> Optional[Type[BaseRule]]:
        return cls._rules.get(rule_id)

    @classmethod
    def all_rules(cls) -> List[Type[BaseRule]]:
        return sorted(cls._rules.values(), key=lambda r: (r.category, r.id))

    @classmethod
    def run_all(cls, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        """Runs all enabled rules against the given context."""
        issues: List[LintIssue] = []
        for rule_cls in cls.all_rules():
            rule_instance = rule_cls()
            if not config.is_rule_enabled(rule_instance.id, rule_instance.default_severity):
                continue
            rule_issues = rule_instance.check(context, config)
            issues.extend(rule_issues)

        # Sort issues by line number (if available) and path
        issues.sort(key=lambda i: (i.line or 999999, i.column or 999999, i.path))
        return issues
