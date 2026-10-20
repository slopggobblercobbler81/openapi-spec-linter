"""Schema, component, and $ref linting rules."""

from typing import Any, Dict, List, Set

from ..models import LintContext, LintIssue, Severity
from ..config import LinterConfig
from .base import BaseRule, RuleRegistry, collect_refs, resolve_local_ref


@RuleRegistry.register
class NoDanglingRefsRule(BaseRule):
    id = "no-dangling-refs"
    name = "No Dangling JSON References"
    description = "All local JSON references ($ref starting with '#/') must resolve to an existing element in the spec."
    category = "schemas"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        spec = context.spec

        def _traverse(node: Any, pointer: str):
            if isinstance(node, dict):
                for k, v in node.items():
                    sub_ptr = f"{pointer}/{k.replace('~', '~0').replace('/', '~1')}"
                    if k == "$ref" and isinstance(v, str):
                        if v.startswith("#/"):
                            _, exists = resolve_local_ref(spec, v)
                            if not exists:
                                issues.append(
                                    self.create_issue(
                                        message=f"Unresolved local reference '{v}'. Target does not exist in the specification.",
                                        path=pointer,
                                        context=context,
                                        config=config,
                                        suggestion=f"Verify that the referenced definition '{v}' exists under components or paths.",
                                    )
                                )
                    else:
                        _traverse(v, sub_ptr)
            elif isinstance(node, list):
                for idx, item in enumerate(node):
                    _traverse(item, f"{pointer}/{idx}")

        _traverse(spec, "")
        return issues


@RuleRegistry.register
class NoUnusedSchemasRule(BaseRule):
    id = "no-unused-schemas"
    name = "No Unused Component Schemas"
    description = "Schemas declared in 'components.schemas' should be referenced elsewhere in the document."
    category = "schemas"
    default_severity = Severity.INFO

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        components = context.spec.get("components")
        if not isinstance(components, dict):
            return issues

        schemas = components.get("schemas")
        if not isinstance(schemas, dict) or not schemas:
            return issues

        # Collect all references across the document outside each schema itself
        all_refs = collect_refs(context.spec)

        for schema_name in schemas.keys():
            expected_ref = f"#/components/schemas/{schema_name}"
            # Check if referenced anywhere
            if expected_ref not in all_refs:
                escaped = schema_name.replace("~", "~0").replace("/", "~1")
                issues.append(
                    self.create_issue(
                        message=f"Schema '{schema_name}' in 'components.schemas' is defined but never referenced.",
                        path=f"/components/schemas/{escaped}",
                        context=context,
                        config=config,
                        suggestion=f"Reference '#/components/schemas/{schema_name}' or remove the unused schema.",
                    )
                )

        return issues


@RuleRegistry.register
class ParameterDescriptionRule(BaseRule):
    id = "param-description"
    name = "Parameter Description Provided"
    description = "All parameters should provide a descriptive explanation of their function."
    category = "schemas"
    default_severity = Severity.WARNING

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []

        def _check_param(param: Any, ptr: str):
            if not isinstance(param, dict) or "$ref" in param:
                return
            p_name = param.get("name", "unknown")
            desc = param.get("description")
            if not desc or not str(desc).strip():
                issues.append(
                    self.create_issue(
                        message=f"Parameter '{p_name}' is missing a description.",
                        path=ptr,
                        context=context,
                        config=config,
                        suggestion=f"Add a 'description' explaining the usage of '{p_name}'.",
                    )
                )

        # Check path item parameters and operation parameters
        paths = context.spec.get("paths")
        if isinstance(paths, dict):
            for path_k, path_item in paths.items():
                if not isinstance(path_item, dict):
                    continue
                escaped_path = path_k.replace("~", "~0").replace("/", "~1")
                for idx, p in enumerate(path_item.get("parameters") or []):
                    _check_param(p, f"/paths/{escaped_path}/parameters/{idx}")

                for method, op in path_item.items():
                    if isinstance(op, dict):
                        for idx, p in enumerate(op.get("parameters") or []):
                            _check_param(p, f"/paths/{escaped_path}/{method}/parameters/{idx}")

        # Check components.parameters
        components = context.spec.get("components")
        if isinstance(components, dict):
            comp_params = components.get("parameters")
            if isinstance(comp_params, dict):
                for p_name, p_obj in comp_params.items():
                    escaped_name = p_name.replace("~", "~0").replace("/", "~1")
                    _check_param(p_obj, f"/components/parameters/{escaped_name}")

        return issues


@RuleRegistry.register
class SchemaDescriptionRule(BaseRule):
    id = "schema-description"
    name = "Component Schema Description"
    description = "Reusable component schemas should provide a description explaining the model."
    category = "schemas"
    default_severity = Severity.INFO

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        components = context.spec.get("components")
        if not isinstance(components, dict):
            return issues

        schemas = components.get("schemas")
        if not isinstance(schemas, dict):
            return issues

        for schema_name, schema_obj in schemas.items():
            if not isinstance(schema_obj, dict) or "$ref" in schema_obj:
                continue
            desc = schema_obj.get("description")
            if not desc or not str(desc).strip():
                escaped = schema_name.replace("~", "~0").replace("/", "~1")
                issues.append(
                    self.create_issue(
                        message=f"Component schema '{schema_name}' has no description.",
                        path=f"/components/schemas/{escaped}",
                        context=context,
                        config=config,
                        suggestion=f"Add a 'description' describing the '{schema_name}' data model.",
                    )
                )

        return issues
