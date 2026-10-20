"""Metadata and specification info linting rules."""

import re
from typing import List

from ..models import LintContext, LintIssue, Severity
from ..config import LinterConfig
from .base import BaseRule, RuleRegistry


@RuleRegistry.register
class OpenAPIVersionRule(BaseRule):
    id = "openapi-version"
    name = "OpenAPI Version Specification"
    description = "Spec must declare a valid OpenAPI 3.0.x or 3.1.x version string."
    category = "info"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        spec = context.spec
        version = spec.get("openapi")

        if not version:
            # Check if swagger 2.0 was used instead
            swagger = spec.get("swagger")
            if swagger:
                issues.append(
                    self.create_issue(
                        message=f"Specification declares Swagger '{swagger}', but OpenAPI 3.0.x or 3.1.x is required.",
                        path="/swagger",
                        context=context,
                        config=config,
                        suggestion="Upgrade specification to OpenAPI 3.0.x or 3.1.x.",
                    )
                )
            else:
                issues.append(
                    self.create_issue(
                        message="Missing required 'openapi' version field at root level.",
                        path="/",
                        context=context,
                        config=config,
                        suggestion="Add 'openapi: \"3.0.3\"' or 'openapi: \"3.1.0\"' to the root.",
                    )
                )
            return issues

        version_str = str(version).strip()
        if not re.match(r"^3\.[01]\.\d+(-.+)?$", version_str):
            issues.append(
                self.create_issue(
                    message=f"Unsupported OpenAPI version '{version_str}'. Must be 3.0.x or 3.1.x.",
                    path="/openapi",
                    context=context,
                    config=config,
                    suggestion="Set 'openapi' to a supported version like '3.0.3' or '3.1.0'.",
                )
            )

        return issues


@RuleRegistry.register
class InfoContactRule(BaseRule):
    id = "info-contact"
    name = "API Contact Information"
    description = "The 'info.contact' object should provide a name, email, or URL for API maintainers."
    category = "info"
    default_severity = Severity.WARNING

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        info = context.spec.get("info")
        if not isinstance(info, dict):
            return issues  # Handled by info-description/root checks

        contact = info.get("contact")
        if not contact or not isinstance(contact, dict):
            issues.append(
                self.create_issue(
                    message="Missing 'info.contact' information.",
                    path="/info",
                    context=context,
                    config=config,
                    suggestion="Add a 'contact' object with 'name', 'email', or 'url' under 'info'.",
                )
            )
            return issues

        has_field = any(contact.get(f) for f in ("name", "email", "url"))
        if not has_field:
            issues.append(
                self.create_issue(
                    message="'info.contact' must contain at least one of 'name', 'email', or 'url'.",
                    path="/info/contact",
                    context=context,
                    config=config,
                    suggestion="Provide at least an 'email' or 'url' in 'info.contact'.",
                )
            )

        return issues


@RuleRegistry.register
class InfoDescriptionRule(BaseRule):
    id = "info-description"
    name = "API Info Description"
    description = "The 'info.description' field must be provided and contain meaningful text."
    category = "info"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        info = context.spec.get("info")
        if not isinstance(info, dict):
            issues.append(
                self.create_issue(
                    message="Missing required 'info' object at root.",
                    path="/",
                    context=context,
                    config=config,
                    suggestion="Define an 'info' section with 'title', 'version', and 'description'.",
                )
            )
            return issues

        desc = info.get("description")
        if not desc or not str(desc).strip():
            issues.append(
                self.create_issue(
                    message="Missing or empty 'info.description'.",
                    path="/info",
                    context=context,
                    config=config,
                    suggestion="Add a descriptive explanation of what the API does under 'info.description'.",
                )
            )
        elif len(str(desc).strip()) < 5:
            issues.append(
                self.create_issue(
                    message="'info.description' is too short to be descriptive (minimum 5 characters).",
                    path="/info/description",
                    context=context,
                    config=config,
                )
            )

        return issues


@RuleRegistry.register
class InfoVersionRule(BaseRule):
    id = "info-version"
    name = "API Version String"
    description = "The 'info.version' field must be defined and non-empty."
    category = "info"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        info = context.spec.get("info")
        if not isinstance(info, dict):
            return issues

        version = info.get("version")
        if not version or not str(version).strip():
            issues.append(
                self.create_issue(
                    message="Missing required 'info.version' string.",
                    path="/info",
                    context=context,
                    config=config,
                    suggestion="Add a version string such as '1.0.0' to 'info.version'.",
                )
            )
        return issues


@RuleRegistry.register
class InfoLicenseRule(BaseRule):
    id = "info-license"
    name = "API License Information"
    description = "The 'info.license' object should define the API license and name."
    category = "info"
    default_severity = Severity.INFO

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        info = context.spec.get("info")
        if not isinstance(info, dict):
            return issues

        license_obj = info.get("license")
        if not license_obj or not isinstance(license_obj, dict):
            issues.append(
                self.create_issue(
                    message="Missing 'info.license' declaration.",
                    path="/info",
                    context=context,
                    config=config,
                    suggestion="Consider adding license information (e.g., Apache 2.0, MIT) under 'info.license'.",
                )
            )
            return issues

        if not license_obj.get("name") or not str(license_obj.get("name")).strip():
            issues.append(
                self.create_issue(
                    message="'info.license.name' must be specified.",
                    path="/info/license",
                    context=context,
                    config=config,
                )
            )
        return issues
