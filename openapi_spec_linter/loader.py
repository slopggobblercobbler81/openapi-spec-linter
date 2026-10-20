"""OpenAPI file loader with source line number mapping for YAML and JSON."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import yaml
from yaml.nodes import MappingNode, SequenceNode, ScalarNode

from .models import LintContext, LintIssue, LintResult, Severity


def escape_pointer_token(token: str) -> str:
    """Escape a JSON pointer token according to RFC 6901."""
    return str(token).replace("~", "~0").replace("/", "~1")


class LineTrackingLoader:
    """Builds a Python object tree and a JSON Pointer -> (line, col) map from YAML/JSON."""

    def __init__(self, content: str):
        self.content = content
        self.line_map: Dict[str, Tuple[int, int]] = {}

    def parse(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Parses the content into a dict, building line_map. Returns (data, error_message)."""
        if not self.content.strip():
            return None, "File is empty"

        # Attempt to parse with PyYAML compose for full AST line tracking
        try:
            node = yaml.compose(self.content, Loader=yaml.SafeLoader)
            if node is None:
                return None, "Document contains no valid YAML/JSON content"
            data = self._node_to_py(node, "")
            if not isinstance(data, dict):
                return None, f"Root element must be a dictionary/object, found {type(data).__name__}"
            return data, None
        except Exception as yaml_err:
            # If yaml parsing failed, fallback to json parsing to see if it's invalid JSON
            try:
                data = json.loads(self.content)
                if not isinstance(data, dict):
                    return None, f"Root element must be a JSON object, found {type(data).__name__}"
                return data, None
            except Exception:
                return None, f"Parse error: {str(yaml_err)}"

    def _node_to_py(self, node: Any, pointer: str) -> Any:
        line = node.start_mark.line + 1
        col = node.start_mark.column + 1
        self.line_map[pointer or "/"] = (line, col)

        if isinstance(node, MappingNode):
            result = {}
            for key_node, val_node in node.value:
                key = yaml.SafeLoader.construct_object(yaml.SafeLoader(self.content), key_node)
                key_str = str(key)
                sub_pointer = f"{pointer}/{escape_pointer_token(key_str)}"
                self.line_map[sub_pointer] = (key_node.start_mark.line + 1, key_node.start_mark.column + 1)
                result[key] = self._node_to_py(val_node, sub_pointer)
            return result
        elif isinstance(node, SequenceNode):
            result = []
            for idx, item_node in enumerate(node.value):
                sub_pointer = f"{pointer}/{idx}"
                self.line_map[sub_pointer] = (item_node.start_mark.line + 1, item_node.start_mark.column + 1)
                result.append(self._node_to_py(item_node, sub_pointer))
            return result
        elif isinstance(node, ScalarNode):
            # Use SafeLoader to cast types (numbers, bools, strings, nulls)
            val = yaml.SafeLoader.construct_scalar(yaml.SafeLoader(self.content), node)
            return val
        return None


def load_spec(file_path: str) -> Tuple[Optional[LintContext], LintResult]:
    """Load an OpenAPI spec from a file path into a LintContext."""
    result = LintResult(file_path=file_path)
    path_obj = Path(file_path)

    if not path_obj.exists():
        msg = f"File not found: {file_path}"
        result.parse_error = msg
        result.issues.append(
            LintIssue(
                rule_id="FILE_NOT_FOUND",
                message=msg,
                severity=Severity.ERROR,
                path="/",
            )
        )
        return None, result

    try:
        content = path_obj.read_text(encoding="utf-8")
    except Exception as e:
        msg = f"Failed to read file: {e}"
        result.parse_error = msg
        result.issues.append(
            LintIssue(
                rule_id="FILE_READ_ERROR",
                message=msg,
                severity=Severity.ERROR,
                path="/",
            )
        )
        return None, result

    loader = LineTrackingLoader(content)
    data, err = loader.parse()

    if err or data is None:
        result.parse_error = err or "Unknown parse error"
        result.issues.append(
            LintIssue(
                rule_id="PARSE_ERROR",
                message=result.parse_error,
                severity=Severity.ERROR,
                path="/",
                line=1,
                column=1,
            )
        )
        return None, result

    version = data.get("openapi") or data.get("swagger")
    result.spec_version = str(version) if version else None

    context = LintContext(
        file_path=file_path,
        raw_content=content,
        spec=data,
        line_map=loader.line_map,
    )
    return context, result


def load_spec_from_string(content: str, file_path: str = "inline.yaml") -> Tuple[Optional[LintContext], LintResult]:
    """Load an OpenAPI spec from raw string content."""
    result = LintResult(file_path=file_path)
    loader = LineTrackingLoader(content)
    data, err = loader.parse()

    if err or data is None:
        result.parse_error = err or "Unknown parse error"
        result.issues.append(
            LintIssue(
                rule_id="PARSE_ERROR",
                message=result.parse_error,
                severity=Severity.ERROR,
                path="/",
                line=1,
                column=1,
            )
        )
        return None, result

    version = data.get("openapi") or data.get("swagger")
    result.spec_version = str(version) if version else None

    context = LintContext(
        file_path=file_path,
        raw_content=content,
        spec=data,
        line_map=loader.line_map,
    )
    return context, result
