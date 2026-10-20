"""Security configuration linting rules."""

from typing import List, Set

from ..models import LintContext, LintIssue, Severity
from ..config import LinterConfig
from .base import BaseRule, RuleRegistry, iter_operations


@RuleRegistry.register
class SecurityDefinedRule(BaseRule):
    id = "security-defined"
    name = "Security Requirements Defined"
    description = "API should define security requirements either globally or at the operation level."
    category = "security"
    default_severity = Severity.INFO

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        spec = context.spec

        # Check global security
        global_security = spec.get("security")
        if isinstance(global_security, list) and len(global_security) > 0:
            return issues

        # Check if operations define security
        has_any_op_security = False
        for _, _, op, _ in iter_operations(spec):
            op_security = op.get("security")
            if isinstance(op_security, list) and len(op_security) > 0:
                has_any_op_security = True
                break

        if not has_any_op_security:
            issues.append(
                self.create_issue(
                    message="No security requirements defined globally in 'security' or within operations.",
                    path="/",
                    context=context,
                    config=config,
                    suggestion="Add a global 'security' array or per-operation security requirements.",
                )
            )

        return issues


@RuleRegistry.register
class SecuritySchemeExistsRule(BaseRule):
    id = "security-scheme-exists"
    name = "Referenced Security Scheme Exists"
    description = "All security schemes referenced in 'security' arrays must be defined in 'components.securitySchemes'."
    category = "security"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        spec = context.spec
        components = spec.get("components") or {}
        defined_schemes: Set[str] = set()

        if isinstance(components, dict):
            sec_schemes = components.get("securitySchemes")
            if isinstance(sec_schemes, dict):
                defined_schemes = set(sec_schemes.keys())

        # Check root security
        global_security = spec.get("security")
        if isinstance(global_security, list):
            for idx, sec_req in enumerate(global_security):
                if isinstance(sec_req, dict):
                    for scheme_name in sec_req.keys():
                        if scheme_name not in defined_schemes:
                            issues.append(
                                self.create_issue(
                                    message=f"Global security requirement references unknown scheme '{scheme_name}'.",
                                    path=f"/security/{idx}/{scheme_name}",
                                    context=context,
                                    config=config,
                                    suggestion=f"Define '{scheme_name}' under 'components.securitySchemes'.",
                                )
                            )

        # Check operation security
        for path, method, op, pointer in iter_operations(spec):
            op_sec = op.get("security")
            if isinstance(op_sec, list):
                for idx, sec_req in enumerate(op_sec):
                    if isinstance(sec_req, dict):
                        for scheme_name in sec_req.keys():
                            if scheme_name not in defined_schemes:
                                issues.append(
                                    self.create_issue(
                                        message=f"Operation {method.upper()} '{path}' references unknown security scheme '{scheme_name}'.",
                                        path=f"{pointer}/security/{idx}/{scheme_name}",
                                        context=context,
                                        config=config,
                                        suggestion=f"Define '{scheme_name}' under 'components.securitySchemes'.",
                                    )
                                )

        return issues
