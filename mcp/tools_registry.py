"""
MCP Tools Registry for InsightShop.

- Loads tool definitions from insight_shop_tools.json.
- Exposes tools for LLM (by role: user vs admin).
- Validates tool name, input schema, and permission before execution.
- Backend enforces these checks; LLM cannot bypass.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

# Path to tool definitions (relative to this file)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOLS_JSON_PATH = os.path.join(_THIS_DIR, "insight_shop_tools.json")

_tools_cache: Optional[List[Dict]] = None


def _load_tools() -> List[Dict]:
    global _tools_cache
    if _tools_cache is None:
        with open(_TOOLS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _tools_cache = data.get("tools", [])
    return _tools_cache


def list_tool_names(role: Optional[str] = None) -> List[str]:
    """Return tool names. If role is 'user', only user tools; if 'admin', user + admin tools."""
    tools = _load_tools()
    if role == "admin":
        return [t["name"] for t in tools]
    if role == "user":
        return [t["name"] for t in tools if t.get("permission") == "user"]
    return [t["name"] for t in tools]


def get_tool_definition(name: str) -> Optional[Dict]:
    """Return the full definition for a tool by name, or None if not found."""
    tools = _load_tools()
    for t in tools:
        if t.get("name") == name:
            return t
    return None


def get_tools_for_llm(role: str = "user") -> List[Dict]:
    """
    Return tools in LLM-friendly format (OpenAI/Anthropic function-calling style).
    role: 'user' -> only user-permission tools; 'admin' -> user + admin tools.
    Each tool: { "name", "description", "parameters": { "type": "object", "properties": {...}, "required": [...] } }
    """
    tools = _load_tools()
    if role == "admin":
        allowed = tools
    else:
        allowed = [t for t in tools if t.get("permission") == "user"]

    result = []
    for t in allowed:
        schema = t.get("input_schema", {})
        # Convert to OpenAI-style parameters (subset of JSON Schema)
        params = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "additionalProperties": schema.get("additionalProperties", False),
        }
        if schema.get("required"):
            params["required"] = schema["required"]
        result.append({
            "name": t["name"],
            "description": t.get("description", ""),
            "parameters": params,
        })
    return result


def _validate_value(value: Any, schema: Dict, path: str = "") -> Optional[str]:
    """Validate a value against a JSON Schema subset. Returns error message or None."""
    if "type" in schema:
        t = schema["type"]
        if t == "string":
            if not isinstance(value, str):
                return f"{path}: expected string, got {type(value).__name__}"
            if "minLength" in schema and len(value) < schema["minLength"]:
                return f"{path}: string too short (min {schema['minLength']})"
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                return f"{path}: string too long (max {schema['maxLength']})"
            if "enum" in schema and value not in schema["enum"]:
                return f"{path}: must be one of {schema['enum']}"
        elif t == "integer":
            if not isinstance(value, (int, float)) or int(value) != value:
                return f"{path}: expected integer, got {type(value).__name__}"
            v = int(value)
            if "minimum" in schema and v < schema["minimum"]:
                return f"{path}: must be >= {schema['minimum']}"
            if "maximum" in schema and v > schema["maximum"]:
                return f"{path}: must be <= {schema['maximum']}"
        elif t == "number":
            if not isinstance(value, (int, float)):
                return f"{path}: expected number, got {type(value).__name__}"
            v = float(value)
            if "minimum" in schema and v < schema["minimum"]:
                return f"{path}: must be >= {schema['minimum']}"
            if "maximum" in schema and v > schema["maximum"]:
                return f"{path}: must be <= {schema['maximum']}"
        elif t == "boolean":
            if not isinstance(value, bool):
                return f"{path}: expected boolean, got {type(value).__name__}"
        elif t == "array":
            if not isinstance(value, list):
                return f"{path}: expected array, got {type(value).__name__}"
            if "minItems" in schema and len(value) < schema["minItems"]:
                return f"{path}: array must have at least {schema['minItems']} items"
            if "maxItems" in schema and len(value) > schema["maxItems"]:
                return f"{path}: array must have at most {schema['maxItems']} items"
            items_schema = schema.get("items", {})
            for i, item in enumerate(value):
                err = _validate_value(item, items_schema, f"{path}[{i}]")
                if err:
                    return err
        elif t == "object":
            if not isinstance(value, dict):
                return f"{path}: expected object, got {type(value).__name__}"
    return None


def _validate_object(obj: Any, schema: Dict, path: str = "") -> Optional[str]:
    """Validate object against schema (required, properties, additionalProperties)."""
    if not isinstance(obj, dict):
        return f"{path}: expected object, got {type(obj).__name__}"
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}).keys())
        for k in obj:
            if k not in allowed:
                return f"{path}: unknown property '{k}'"
    for req in schema.get("required", []):
        if req not in obj:
            return f"{path}: missing required property '{req}'"
    for prop, prop_schema in schema.get("properties", {}).items():
        if prop not in obj:
            continue
        err = _validate_value(obj[prop], prop_schema, f"{path}.{prop}")
        if err:
            return err
    return None


def validate_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    is_admin: bool,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a tool call: tool exists, input matches schema, user has permission.
    arguments: the JSON object the LLM passed as tool arguments.
    is_admin: True if current user is admin (e.g. is_superadmin).
    Returns (valid, error_message). If valid, error_message is None.
    """
    definition = get_tool_definition(tool_name)
    if not definition:
        return False, "Tool not found"

    permission = definition.get("permission", "user")
    if permission == "admin" and not is_admin:
        return False, "Admin permission required"

    schema = definition.get("input_schema", {})
    if not schema:
        return True, None

    err = _validate_object(arguments, schema, "input")
    if err:
        return False, err
    return True, None


def validate_and_sanitize_args(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure only allowed keys are present (additionalProperties: false).
    Does not validate types; use validate_tool_call for full validation.
    """
    definition = get_tool_definition(tool_name)
    if not definition:
        return arguments
    schema = definition.get("input_schema", {})
    if schema.get("additionalProperties") is not False:
        return arguments
    allowed = set(schema.get("properties", {}).keys())
    return {k: v for k, v in arguments.items() if k in allowed}
