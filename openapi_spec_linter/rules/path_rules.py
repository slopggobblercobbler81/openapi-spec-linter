"""Path and operation linting rules."""

import re
from typing import Dict, List, Set

from ..models import LintContext, LintIssue, Severity
from ..config import LinterConfig
from .base import BaseRule, RuleRegistry, iter_operations


PATH_PARAM_REGEX = re.compile(r"\{([a-zA-Z0-9_.-]+)\}")
IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")


@RuleRegistry.register
class PathTrailingSlashRule(BaseRule):
    id = "path-no-trailing-slash"
    name = "No Trailing Slashes in Paths"
    description = "API endpoint paths must not end with a trailing slash unless the path is root ('/')."
    category = "paths"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        paths = context.spec.get("paths")
        if not isinstance(paths, dict):
            return issues

        for path_str in paths.keys():
            if path_str != "/" and path_str.endswith("/"):
                escaped = path_str.replace("~", "~0").replace("/", "~1")
                suggested = path_str.rstrip("/")
                issues.append(
                    self.create_issue(
                        message=f"Path '{path_str}' must not end with a trailing slash.",
                        path=f"/paths/{escaped}",
                        context=context,
                        config=config,
                        suggestion=f"Rename '{path_str}' to '{suggested}'.",
                    )
                )

        return issues


@RuleRegistry.register
class PathParametersMatchRule(BaseRule):
    id = "path-parameters-match"
    name = "Path Template and Parameter Synchronization"
    description = "Every {param} in path templates must have a corresponding parameter with 'in: path', and vice versa."
    category = "paths"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        paths = context.spec.get("paths")
        if not isinstance(paths, dict):
            return issues

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            escaped_path = path_str.replace("~", "~0").replace("/", "~1")
            template_params: Set[str] = set(PATH_PARAM_REGEX.findall(path_str))

            # Common path item level parameters
            common_params = path_item.get("parameters") or []
            common_path_params = {
                p.get("name")
                for p in common_params
                if isinstance(p, dict) and p.get("in") == "path" and p.get("name")
            }

            for path, method, op, pointer in iter_operations(context.spec):
                if path != path_str:
                    continue

                op_params = op.get("parameters") or []
                op_path_params = {
                    p.get("name")
                    for p in op_params
                    if isinstance(p, dict) and p.get("in") == "path" and p.get("name")
                }

                combined_path_params = common_path_params | op_path_params

                # Check for template variables missing parameter definitions
                for param in template_params:
                    if param not in combined_path_params:
                        issues.append(
                            self.create_issue(
                                message=f"Path template variable '{{{param}}}' in '{path_str}' has no matching 'in: path' parameter definition in operation {method.upper()}.",
                                path=pointer,
                                context=context,
                                config=config,
                                suggestion=f"Define parameter '{param}' with 'in: path' under parameters.",
                            )
                        )

                # Check for defined path parameters missing from template
                for param in combined_path_params:
                    if param not in template_params:
                        issues.append(
                            self.create_issue(
                                message=f"Parameter '{param}' defines 'in: path' but is not present as '{{{param}}}' in path '{path_str}'.",
                                path=f"{pointer}/parameters",
                                context=context,
                                config=config,
                                suggestion=f"Add '{{{param}}}' to path '{path_str}' or change parameter 'in' location.",
                            )
                        )

        return issues


@RuleRegistry.register
class OperationDescriptionRule(BaseRule):
    id = "operation-description"
    name = "Operation Description Defined"
    description = "Every operation must define a non-empty description."
    category = "paths"
    default_severity = Severity.WARNING

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            desc = op.get("description")
            if not desc or not str(desc).strip():
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' is missing a description.",
                        path=pointer,
                        context=context,
                        config=config,
                        suggestion="Add a detailed 'description' explaining what this operation does.",
                    )
                )
            elif len(str(desc).strip()) < 5:
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' description is too short (min 5 chars).",
                        path=f"{pointer}/description",
                        context=context,
                        config=config,
                    )
                )
        return issues


@RuleRegistry.register
class OperationSummaryRule(BaseRule):
    id = "operation-summary"
    name = "Operation Summary Defined"
    description = "Every operation should define a short, human-readable summary."
    category = "paths"
    default_severity = Severity.WARNING

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            summary = op.get("summary")
            if not summary or not str(summary).strip():
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' is missing a summary.",
                        path=pointer,
                        context=context,
                        config=config,
                        suggestion="Add a short 'summary' field (e.g. 'Get user by ID').",
                    )
                )
        return issues


@RuleRegistry.register
class OperationTagsRule(BaseRule):
    id = "operation-tags"
    name = "Operation Tags Specified"
    description = "Every operation should be categorized with at least one tag."
    category = "paths"
    default_severity = Severity.WARNING

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            tags = op.get("tags")
            if not tags or not isinstance(tags, list) or len(tags) == 0:
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' has no tags defined.",
                        path=pointer,
                        context=context,
                        config=config,
                        suggestion="Assign at least one tag to group this operation.",
                    )
                )
        return issues


@RuleRegistry.register
class OperationIdRule(BaseRule):
    id = "operation-id"
    name = "Operation ID Specified"
    description = "Operations should specify an operationId for SDK and documentation generation."
    category = "paths"
    default_severity = Severity.WARNING

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            op_id = op.get("operationId")
            if not op_id or not str(op_id).strip():
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' is missing an 'operationId'.",
                        path=pointer,
                        context=context,
                        config=config,
                        suggestion=f"Add a unique 'operationId' such as '{method}_{path.strip('/').replace('/', '_')}'.",
                    )
                )
        return issues


@RuleRegistry.register
class OperationIdUniqueRule(BaseRule):
    id = "operation-id-unique"
    name = "Unique Operation IDs"
    description = "Each operationId must be globally unique across the entire specification."
    category = "paths"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        seen_ids: Dict[str, str] = {}  # op_id -> pointer

        for path, method, op, pointer in iter_operations(context.spec):
            op_id = op.get("operationId")
            if not op_id or not isinstance(op_id, str):
                continue

            clean_id = op_id.strip()
            if clean_id in seen_ids:
                prev_pointer = seen_ids[clean_id]
                issues.append(
                    self.create_issue(
                        message=f"Duplicate operationId '{clean_id}' found in {method.upper()} '{path}' (previously defined at {prev_pointer}).",
                        path=f"{pointer}/operationId",
                        context=context,
                        config=config,
                        suggestion="Assign a distinct operationId to each endpoint.",
                    )
                )
            else:
                seen_ids[clean_id] = pointer

        return issues


@RuleRegistry.register
class OperationIdCasingRule(BaseRule):
    id = "operation-id-casing"
    name = "Operation ID Valid Format"
    description = "Operation IDs should use alphanumeric characters, underscores, or hyphens without spaces."
    category = "paths"
    default_severity = Severity.INFO

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            op_id = op.get("operationId")
            if isinstance(op_id, str) and op_id.strip():
                clean = op_id.strip()
                if not IDENTIFIER_REGEX.match(clean):
                    issues.append(
                        self.create_issue(
                            message=f"operationId '{clean}' contains invalid characters or spaces.",
                            path=f"{pointer}/operationId",
                            context=context,
                            config=config,
                            suggestion="Use camelCase, snake_case, or kebab-case for operationId.",
                        )
                    )
        return issues
