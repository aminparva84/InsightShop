# InsightShop MCP Tools

This package defines **MCP (Model Context Protocol) tools** for the InsightShop AI chat: each tool has a **name**, **description**, **strict input schema**, and **permission level** (user vs admin).

**The existing AI agent is unchanged.** The chat still uses `utils/agent_executor.py` (actions `add_item`, `remove_item`, `show_cart`, `clear_cart`). This MCP layer is optional and additive; use it when you want schema-based tools and validation (e.g. for a new LLM integration). See `docs/mcp-tools-design.md` for compatibility and mapping (MCP `cart_add_item` ↔ agent `add_item`, etc.).

## Files

- **`insight_shop_tools.json`** — Single source of truth for all tools (name, description, permission, input_schema).
- **`tools_registry.py`** — Loads the JSON, exposes tools for the LLM by role, and validates tool calls (tool exists, input matches schema, user has permission).

## Usage

### Get tools for the LLM (by role)

```python
from mcp import get_tools_for_llm

# For a normal user (or guest): only user-permission tools
user_tools = get_tools_for_llm("user")

# For an admin: user + admin tools
admin_tools = get_tools_for_llm("admin")
```

Each item has `name`, `description`, and `parameters` (OpenAI/Anthropic-style JSON Schema).

### Validate before executing

**Always** validate a tool call before running it. The LLM cannot bypass this.

```python
from mcp import validate_tool_call

# After the LLM returns a tool call:
tool_name = "cart_add_item"
arguments = {"clothing_type": "shirt", "selected_color": "white", "quantity": 2}
is_admin = getattr(current_user, "is_superadmin", False) if current_user else False

valid, error_message = validate_tool_call(tool_name, arguments, is_admin)
if not valid:
    # Return error to agent; do not execute
    return {"error": error_message}
# Else: execute via existing backend (e.g. agent_executor.execute_action)
```

### List tool names

```python
from mcp import list_tool_names

list_tool_names("user")   # Only user tools
list_tool_names("admin")  # All tools
list_tool_names()         # All tools
```

### Get one tool definition

```python
from mcp import get_tool_definition

defn = get_tool_definition("cart_add_item")
# defn["name"], defn["description"], defn["permission"], defn["input_schema"]
```

## Design and flow

See **`docs/mcp-tools-design.md`** for:

- End-to-end flow (chat → LLM → tool call or message → validate → execute → result → final message).
- Full list of user and admin tools with strict input schemas.
- Enforcement checklist (tool exists, schema valid, permission).
- Integration example with the AI chat route.

## Adding or changing tools

1. Edit **`insight_shop_tools.json`**: add or update an entry under `tools` with `name`, `description`, `permission` (`"user"` or `"admin"`), and `input_schema` (JSON Schema with `type`, `required`, `properties`, `additionalProperties`).
2. Implement execution in the backend (routes or `utils/agent_executor.py`) so that when the validated tool is invoked, the correct API or DB logic runs.
3. Optionally extend `tools_registry.validate_tool_call` if you use schema features beyond the current subset (e.g. `format`, `pattern`).
