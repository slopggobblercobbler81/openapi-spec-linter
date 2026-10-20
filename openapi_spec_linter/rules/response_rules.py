"""Response and HTTP status code linting rules."""

from typing import List, Set

from ..models import LintContext, LintIssue, Severity
from ..config import LinterConfig
from .base import BaseRule, RuleRegistry, iter_operations


# IANA registered standard HTTP status codes
STANDARD_HTTP_STATUS_CODES: Set[str] = {
    # 1xx Informational
    "100", "101", "102", "103",
    # 2xx Success
    "200", "201", "202", "203", "204", "205", "206", "207", "208", "226",
    # 3xx Redirection
    "300", "301", "302", "303", "304", "305", "307", "308",
    # 4xx Client Error
    "400", "401", "402", "403", "404", "405", "406", "407", "408", "409",
    "410", "411", "412", "413", "414", "415", "416", "417", "418", "421",
    "422", "423", "424", "425", "426", "428", "429", "431", "451",
    # 5xx Server Error
    "500", "501", "502", "503", "504", "505", "506", "507", "508", "510", "511",
    # Wildcards & Default allowed by OpenAPI
    "1XX", "2XX", "3XX", "4XX", "5XX", "default"
}


@RuleRegistry.register
class ValidStatusCodeRule(BaseRule):
    id = "valid-status-code"
    name = "Standard HTTP Response Codes"
    description = "Response keys must be standard IANA HTTP status codes (e.g. 200, 404, 500), wildcards (2XX), or 'default'."
    category = "responses"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        user_allowed = set(str(c) for c in config.options.get("allowed_status_codes", []))
        valid_codes = STANDARD_HTTP_STATUS_CODES | user_allowed

        for path, method, op, pointer in iter_operations(context.spec):
            responses = op.get("responses")
            if not isinstance(responses, dict):
                continue

            for status_code, resp_obj in responses.items():
                code_str = str(status_code).strip()
                if code_str.upper() not in valid_codes and code_str not in valid_codes:
                    issues.append(
                        self.create_issue(
                            message=f"Non-standard HTTP status code '{code_str}' in {method.upper()} '{path}'. Must be a recognized 3-digit IANA status code or 'default'.",
                            path=f"{pointer}/responses/{code_str}",
                            context=context,
                            config=config,
                            suggestion="Use standard status codes (e.g., 200 OK, 201 Created, 400 Bad Request, 404 Not Found).",
                        )
                    )

        return issues


@RuleRegistry.register
class ResponseDescriptionRule(BaseRule):
    id = "response-description"
    name = "Response Description Required"
    description = "Every response object must include a non-empty description (as mandated by OpenAPI specification)."
    category = "responses"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            responses = op.get("responses")
            if not isinstance(responses, dict):
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' is missing a 'responses' object.",
                        path=pointer,
                        context=context,
                        config=config,
                        suggestion="Define at least one HTTP response under 'responses'.",
                    )
                )
                continue

            for status_code, resp_obj in responses.items():
                code_str = str(status_code)
                resp_pointer = f"{pointer}/responses/{code_str}"
                if not isinstance(resp_obj, dict):
                    continue

                # If it's a reference, we skip checking local description unless resolved
                if "$ref" in resp_obj:
                    continue

                desc = resp_obj.get("description")
                if not desc or not str(desc).strip():
                    issues.append(
                        self.create_issue(
                            message=f"Response '{code_str}' in {method.upper()} '{path}' is missing a required 'description'.",
                            path=resp_pointer,
                            context=context,
                            config=config,
                            suggestion=f"Add a 'description' such as 'Successful response' to response '{code_str}'.",
                        )
                    )
                elif len(str(desc).strip()) < 3:
                    issues.append(
                        self.create_issue(
                            message=f"Response '{code_str}' description in {method.upper()} '{path}' is too short.",
                            path=f"{resp_pointer}/description",
                            context=context,
                            config=config,
                        )
                    )

        return issues


@RuleRegistry.register
class SuccessResponsePresentRule(BaseRule):
    id = "success-response-present"
    name = "Success Response Defined"
    description = "Every operation must define at least one successful response (2xx code or 2XX wildcard)."
    category = "responses"
    default_severity = Severity.ERROR

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            responses = op.get("responses")
            if not isinstance(responses, dict) or not responses:
                continue

            has_success = False
            for code in responses.keys():
                code_str = str(code).upper()
                if (code_str.isdigit() and 200 <= int(code_str) <= 299) or code_str == "2XX":
                    has_success = True
                    break

            if not has_success:
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' does not define any 2xx success response.",
                        path=f"{pointer}/responses",
                        context=context,
                        config=config,
                        suggestion="Define a '200' or '201' response for successful execution.",
                    )
                )

        return issues


@RuleRegistry.register
class ResponseContentDefinedRule(BaseRule):
    id = "response-content-defined"
    name = "Response Content Media Type"
    description = "Successful responses (200, 201) should define content media types and schemas (unless 204 No Content)."
    category = "responses"
    default_severity = Severity.WARNING

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            responses = op.get("responses")
            if not isinstance(responses, dict):
                continue

            for code in ("200", "201"):
                if code in responses:
                    resp_obj = responses[code]
                    if isinstance(resp_obj, dict) and "$ref" not in resp_obj:
                        content = resp_obj.get("content")
                        if not content or not isinstance(content, dict) or len(content) == 0:
                            issues.append(
                                self.create_issue(
                                    message=f"Response '{code}' in {method.upper()} '{path}' does not define a 'content' media type schema.",
                                    path=f"{pointer}/responses/{code}",
                                    context=context,
                                    config=config,
                                    suggestion="Define 'content: application/json: schema: ...' for data responses.",
                                )
                            )

        return issues


@RuleRegistry.register
class ErrorResponsePresentRule(BaseRule):
    id = "error-response-present"
    name = "Error Response Defined"
    description = "Operations should specify at least one error response (4xx, 5xx, or 'default') to document error states."
    category = "responses"
    default_severity = Severity.INFO

    def check(self, context: LintContext, config: LinterConfig) -> List[LintIssue]:
        issues = []
        for path, method, op, pointer in iter_operations(context.spec):
            responses = op.get("responses")
            if not isinstance(responses, dict) or not responses:
                continue

            has_error = False
            for code in responses.keys():
                code_str = str(code).upper()
                if (code_str.isdigit() and 400 <= int(code_str) <= 599) or code_str in ("4XX", "5XX", "DEFAULT"):
                    has_error = True
                    break

            if not has_error:
                issues.append(
                    self.create_issue(
                        message=f"Operation {method.upper()} '{path}' does not define any 4xx/5xx or default error response.",
                        path=f"{pointer}/responses",
                        context=context,
                        config=config,
                        suggestion="Define '400', '404', or 'default' error responses.",
                    )
                )

        return issues
