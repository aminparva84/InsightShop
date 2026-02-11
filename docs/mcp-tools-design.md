# MCP Tools Design for InsightShop

This document defines **Model Context Protocol (MCP) tools** for the InsightShop AI chat flow. Each tool has a **Name**, **Description**, **Strict input schema**, and **Permission level** (user vs admin). The backend enforces permissions and schema validation before execution; the LLM cannot bypass this.

---

## Compatibility with the existing agent

**The current AI agent was not modified.** The chat flow still uses:

- **`utils/agent_executor.py`** — actions `add_item`, `remove_item`, `show_cart`, `clear_cart`, `none`; `parse_agent_response`, `can_execute_action`, `execute_action`.
- **`routes/ai_agent.py`** — cart-intent detection, `AGENT_SYSTEM_PROMPT`, and the same permission checks as before.

The MCP tools in this doc and in `mcp/` are **additive**: they are a design and a registry you can use when you want to expose a richer, schema-driven tool set (e.g. for a different LLM integration or a future refactor). They do **not** replace or conflict with the existing agent.

If you later wire MCP into the same chat endpoint, use the mapping below so MCP tool names and params align with the existing executor:

| MCP tool           | Existing agent action | Param mapping |
|-------------------|------------------------|---------------|
| `cart_add_item`   | `add_item`             | `selected_color` → `color`, `selected_size` → `size`; rest same |
| `cart_remove_item`| `remove_item`          | same |
| `cart_show`       | `show_cart`            | (no params) |
| `cart_clear`      | `clear_cart`           | (no params) |

Validate with `validate_tool_call(mcp_tool_name, args, is_admin)` then translate to `execute_action(agent_action, params)` using the table above.

---

## Flow Overview

1. **Chat input** (e.g. *"add 2 large white shirts into my cart"*) arrives.
2. **System instructions** + **Tool definitions (MCP)** + **User message** + **Context (role, permissions)** are sent to the LLM.
3. **Rule for the LLM:** *"You may only act by calling tools. If no tool applies, respond normally."*
4. **LLM output** is one of:
   - **Normal text:** `{ "type": "message", "content": "..." }`
   - **Tool call:** structured output (e.g. OpenAI/Anthropic function calling).
5. **Before execution:** Check tool exists → Input matches schema → User has permission. Reject or sanitize if needed. **Admins vs users are enforced here; the LLM does not get to bypass this.**
6. **Execute tool:** Backend calls internal APIs / DB, handles errors, returns a **clean result**.
7. **Send tool result back to the agent** (e.g. *"Tool cart_add_item returned success"*).
8. **LLM generates the final user-facing message** using the tool result as context.
9. **Response shown in chat.**

---

## Permission Levels

- **user** — Any authenticated or guest user. Can use: login, logout, reviews, cart (own), search, compare, checkout.
- **admin** — User with `is_superadmin` (or `is_admin` where noted). Can do everything a user can, plus: admin panel, products CRUD, orders view/status, sales CRUD and automation, clear any user’s cart, delete any review.

---

## User Tools

### 1. `auth_login`

**Description:** Log in with email and password. Returns a JWT and user info. Use when the user says they want to log in or sign in.

**Permission:** user (unauthenticated allowed for this tool only).

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["email", "password"],
  "additionalProperties": false,
  "properties": {
    "email": { "type": "string", "format": "email", "maxLength": 255 },
    "password": { "type": "string", "minLength": 1, "maxLength": 512 }
  }
}
```

**Backend:** `POST /api/auth/login` with `{ "email", "password" }`.

---

### 2. `auth_logout`

**Description:** Log out the current user. Invalidates or forgets the session/token on the server if applicable; client should discard the token. Use when the user says they want to log out or sign out.

**Permission:** user (authenticated or not; no-op if not logged in).

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

**Backend:** No body required. Client clears token; optional `POST /api/auth/logout` if you add it.

---

### 3. `search_products`

**Description:** Search for products by query and optional filters (category, size, max price, sort). Use when the user wants to find, search, or browse items.

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": { "type": "string", "maxLength": 500 },
    "category": { "type": "string", "enum": ["men", "women", "kids"], "default": "" },
    "size": { "type": "string", "maxLength": 20 },
    "max_price": { "type": "number", "minimum": 0, "maximum": 100000 },
    "sort_by": {
      "type": "string",
      "enum": ["relevance", "rating", "price_low", "price_high"],
      "default": "relevance"
    }
  }
}
```

**Backend:** `POST /api/products/search` with `query`, `category`, `size`, `max_price`, `sort_by`.

---

### 4. `cart_add_item`

**Description:** Add one or more units of a product to the current user’s (or guest) cart. Can identify the product by `product_id` or by `color` and `clothing_type` (e.g. “large white shirts”). Use when the user says to add items to cart (e.g. “add 2 large white shirts into my cart”).

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "product_id": { "type": "integer", "minimum": 1 },
    "quantity": { "type": "integer", "minimum": 1, "maximum": 10, "default": 1 },
    "selected_color": { "type": "string", "maxLength": 50 },
    "selected_size": { "type": "string", "maxLength": 20 },
    "clothing_type": { "type": "string", "maxLength": 100 },
    "category": { "type": "string", "enum": ["men", "women", "kids"] }
  }
}
```

**Note:** Either `product_id` OR (`clothing_type` and optionally `selected_color`, `selected_size`, `category`) must be provided so the backend can resolve the product. Backend uses existing resolution (e.g. `resolve_products` in `agent_executor`).

**Backend:** `POST /api/cart` with `product_id`, `quantity`, `selected_color`, `selected_size`; or use existing `execute_add_item` flow.

---

### 5. `cart_remove_item`

**Description:** Remove some or all units of a product from the current user’s (or guest) cart. Can specify `product_id` or `color`/`clothing_type`, and optional `quantity` (default: remove all of that line). Use when the user says to remove or delete items from cart.

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "product_id": { "type": "integer", "minimum": 1 },
    "quantity": { "type": "integer", "minimum": 1, "maximum": 100 },
    "selected_color": { "type": "string", "maxLength": 50 },
    "selected_size": { "type": "string", "maxLength": 20 },
    "clothing_type": { "type": "string", "maxLength": 100 }
  }
}
```

**Backend:** Resolve item then `DELETE /api/cart/<item_id>` or use `execute_remove_item`.

---

### 6. `cart_show`

**Description:** Return the current cart contents (items, quantities, subtotals, total). Use when the user asks to see their cart, what’s in the cart, or show cart.

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

**Backend:** `GET /api/cart` or `execute_show_cart`.

---

### 7. `cart_clear`

**Description:** Clear the current user’s (or guest) cart. Use when the user says to clear, empty, or remove everything from the cart.

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

**Backend:** `DELETE /api/cart/clear` or `execute_clear_cart`.

---

### 8. `compare_products`

**Description:** Compare two or more products by ID (price, category, color, etc.). Use when the user wants to compare items (e.g. “compare product 1, 2, 3” or “compare these items”).

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["product_ids"],
  "additionalProperties": false,
  "properties": {
    "product_ids": {
      "type": "array",
      "minItems": 2,
      "maxItems": 10,
      "items": { "type": "integer", "minimum": 1 }
    }
  }
}
```

**Backend:** `POST /api/ai/compare` with `{ "product_ids": [ ... ] }`.

---

### 9. `review_create`

**Description:** Create a review for a product (rating 1–5 and optional comment). Use when the user wants to write or submit a review for a product.

**Permission:** user (authenticated or guest with `user_name`).

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["product_id", "rating"],
  "additionalProperties": false,
  "properties": {
    "product_id": { "type": "integer", "minimum": 1 },
    "rating": { "type": "number", "minimum": 1.0, "maximum": 5.0 },
    "comment": { "type": "string", "maxLength": 2000 },
    "user_name": { "type": "string", "maxLength": 255 }
  }
}
```

**Backend:** `POST /api/products/<product_id>/reviews` with `rating`, `comment`, `user_name`.

---

### 10. `checkout_proceed`

**Description:** Create an order from the current cart and optionally start payment (e.g. create payment intent). Requires shipping details. Use when the user says to proceed to checkout, place order, or buy.

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "required": [
    "shipping_name",
    "shipping_address",
    "shipping_city",
    "shipping_state",
    "shipping_zip",
    "email"
  ],
  "additionalProperties": false,
  "properties": {
    "email": { "type": "string", "format": "email", "maxLength": 255 },
    "shipping_name": { "type": "string", "minLength": 1, "maxLength": 255 },
    "shipping_address": { "type": "string", "minLength": 1, "maxLength": 500 },
    "shipping_city": { "type": "string", "minLength": 1, "maxLength": 100 },
    "shipping_state": { "type": "string", "minLength": 1, "maxLength": 100 },
    "shipping_zip": { "type": "string", "minLength": 1, "maxLength": 20 },
    "shipping_country": { "type": "string", "maxLength": 50 },
    "shipping_phone": { "type": "string", "maxLength": 30 }
  }
}
```

**Backend:** `POST /api/orders` with shipping + email; then `POST /api/payments/create-intent` with `order_id` for payment. Return order id and payment client secret or mock result.

---

### 11. `order_status`

**Description:** Get the status of an order by order ID and email (for verification). Use when the user asks for order status or tracking.

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["order_id", "email"],
  "additionalProperties": false,
  "properties": {
    "order_id": { "type": "integer", "minimum": 1 },
    "email": { "type": "string", "format": "email", "maxLength": 255 }
  }
}
```

**Backend:** `POST /api/orders/status` with `order_id`, `email`.

---

### 12. `order_track`

**Description:** Get tracking info for a shipment by tracking number. Use when the user asks to track a shipment.

**Permission:** user.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["tracking_number"],
  "additionalProperties": false,
  "properties": {
    "tracking_number": { "type": "string", "minLength": 1, "maxLength": 100 }
  }
}
```

**Backend:** `POST /api/orders/track` with `tracking_number`.

---

## Admin-Only Tools

Admin tools require `is_superadmin` (or `is_admin` where you choose). Admins can also use all user tools.

---

### 13. `admin_product_create`

**Description:** Create a new product (name, price, category, optional fields). Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["name", "price", "category"],
  "additionalProperties": false,
  "properties": {
    "name": { "type": "string", "minLength": 1, "maxLength": 255 },
    "description": { "type": "string", "maxLength": 10000 },
    "price": { "type": "number", "minimum": 0 },
    "category": { "type": "string", "enum": ["men", "women", "kids"] },
    "stock_quantity": { "type": "integer", "minimum": 0 },
    "color": { "type": "string", "maxLength": 50 },
    "size": { "type": "string", "maxLength": 20 },
    "available_colors": { "type": "array", "items": { "type": "string" } },
    "available_sizes": { "type": "array", "items": { "type": "string" } },
    "image_url": { "type": "string", "maxLength": 500 },
    "is_active": { "type": "boolean" }
  }
}
```

**Backend:** `POST /api/admin/products` with same fields.

---

### 14. `admin_product_update`

**Description:** Update an existing product by ID. Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["product_id"],
  "additionalProperties": false,
  "properties": {
    "product_id": { "type": "integer", "minimum": 1 },
    "name": { "type": "string", "minLength": 1, "maxLength": 255 },
    "description": { "type": "string", "maxLength": 10000 },
    "price": { "type": "number", "minimum": 0 },
    "category": { "type": "string", "enum": ["men", "women", "kids"] },
    "stock_quantity": { "type": "integer", "minimum": 0 },
    "color": { "type": "string", "maxLength": 50 },
    "size": { "type": "string", "maxLength": 20 },
    "available_colors": { "type": "array", "items": { "type": "string" } },
    "available_sizes": { "type": "array", "items": { "type": "string" } },
    "image_url": { "type": "string", "maxLength": 500 },
    "is_active": { "type": "boolean" }
  }
}
```

**Backend:** `PUT /api/admin/products/<product_id>`.

---

### 15. `admin_product_delete`

**Description:** Soft-delete a product (set inactive). Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["product_id"],
  "additionalProperties": false,
  "properties": {
    "product_id": { "type": "integer", "minimum": 1 }
  }
}
```

**Backend:** `DELETE /api/admin/products/<product_id>`.

---

### 16. `admin_orders_list`

**Description:** List orders with optional filters (status, user_id, search, pagination). Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "page": { "type": "integer", "minimum": 1 },
    "per_page": { "type": "integer", "minimum": 1, "maximum": 100 },
    "status": { "type": "string", "enum": ["pending", "processing", "shipped", "delivered", "cancelled"] },
    "user_id": { "type": "integer", "minimum": 1 },
    "search": { "type": "string", "maxLength": 200 }
  }
}
```

**Backend:** `GET /api/admin/orders` with query params.

---

### 17. `admin_order_update_status`

**Description:** Change an order’s status. Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["order_id", "status"],
  "additionalProperties": false,
  "properties": {
    "order_id": { "type": "integer", "minimum": 1 },
    "status": {
      "type": "string",
      "enum": ["pending", "processing", "shipped", "delivered", "cancelled"]
    }
  }
}
```

**Backend:** `PUT /api/admin/orders/<order_id>/status` with `{ "status": "..." }`.

---

### 18. `admin_sale_create`

**Description:** Create a new sale (name, discount %, start/end dates). Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["name", "discount_percentage", "start_date", "end_date"],
  "additionalProperties": false,
  "properties": {
    "name": { "type": "string", "minLength": 1, "maxLength": 255 },
    "description": { "type": "string", "maxLength": 1000 },
    "discount_percentage": { "type": "number", "minimum": 0, "maximum": 100 },
    "start_date": { "type": "string", "format": "date", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
    "end_date": { "type": "string", "format": "date", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
    "is_active": { "type": "boolean" },
    "auto_activate": { "type": "boolean" }
  }
}
```

**Backend:** `POST /api/admin/sales` with same fields.

---

### 19. `admin_sale_run_automation`

**Description:** Run the sale automation (activate/sync holiday sales, etc.). Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

**Backend:** `POST /api/admin/sales/run-automation`.

---

### 20. `admin_cart_clear_user`

**Description:** Clear a specific user’s cart (by user_id). Admin only. Use in cart management panel.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["user_id"],
  "additionalProperties": false,
  "properties": {
    "user_id": { "type": "integer", "minimum": 1 }
  }
}
```

**Backend:** `DELETE /api/admin/carts/user/<user_id>`.

---

### 21. `admin_review_delete`

**Description:** Delete any review by ID. Admin only.

**Permission:** admin.

**Strict input schema:**

```json
{
  "type": "object",
  "required": ["review_id"],
  "additionalProperties": false,
  "properties": {
    "review_id": { "type": "integer", "minimum": 1 }
  }
}
```

**Backend:** `DELETE /api/admin/reviews/<review_id>`.

---

## Enforcement Checklist (Before Execute)

For every tool call from the LLM:

1. **Tool exists:** Name must be in the registered tools list (user + admin tools).
2. **Input matches schema:** Validate arguments with the strict JSON Schema above; reject or strip unknown properties.
3. **User has permission:** If tool is `admin`, require `request.current_user.is_superadmin` (or your admin check). Otherwise allow user/guest as per tool.
4. **Reject or sanitize** if any check fails; return a clear error to the agent (e.g. “Tool not allowed” or “Invalid input: …”).
5. **Execute** only after all checks pass; then return a clean result to the agent for the final message.

---

## Example: “add 2 large white shirts into my cart”

1. User message sent to LLM with system prompt and tool list (and context: role = user).
2. LLM returns a tool call, e.g. `cart_add_item` with `{ "clothing_type": "shirt", "selected_color": "white", "selected_size": "large", "quantity": 2 }`.
3. Backend: tool exists ✓, schema valid ✓, user permission ✓ → execute (e.g. resolve “white shirt” + size “large”, then add to cart with quantity 2).
4. Result: `{ "success": true, "message": "Added 2 item(s) to your cart.", "added": [ { "product_id": 31, "name": "...", "quantity": 2 } ] }`.
5. This result is sent back to the LLM as context.
6. LLM replies: “I’ve added 2 large white shirts to your cart.”
7. Response shown in chat.

This design keeps all privilege and input validation on the backend; the LLM only chooses which tool to call and with what arguments, within the defined schemas and permissions.

---

## Integration with Backend

Tool definitions and validation live in the `mcp/` package.

- **Definitions:** `mcp/insight_shop_tools.json` (name, description, permission, input_schema per tool).
- **Registry:** `mcp/tools_registry.py` loads the JSON and exposes:
  - `get_tools_for_llm(role)` — tools in OpenAI/Anthropic function-calling format for the current role (`"user"` or `"admin"`).
  - `get_tool_definition(name)` — full definition for one tool.
  - `validate_tool_call(tool_name, arguments, is_admin)` — returns `(valid: bool, error_message: str | None)`. Call this **before** executing any tool.

**Example: use in the AI chat route**

1. Determine role: `is_admin = getattr(request.current_user, "is_superadmin", False) if get_current_user_optional() else False` (and optionally treat verified user as `"user"`).
2. When building the LLM request, attach tools: `tools = get_tools_for_llm("admin" if is_admin else "user")`.
3. When the LLM returns a tool call (e.g. `cart_add_item` with `{"clothing_type": "shirt", "selected_color": "white", "selected_size": "large", "quantity": 2}`):
   - `valid, err = validate_tool_call(tool_name, arguments, is_admin)`
   - If not valid: return a clean error to the agent (e.g. "Tool not allowed" or `err`) and do **not** execute.
   - If valid: execute via existing logic (e.g. `execute_action` in `utils/agent_executor.py` for cart actions, or internal API calls for auth/search/review/checkout/admin).
4. Return the tool result to the LLM so it can generate the final user-facing message.

**System instruction for the LLM**

Include this (or equivalent) in the system prompt when using tools:

*"You may only act by calling tools. If no tool applies, respond normally with a message. Do not invent or assume tool parameters; use only the arguments defined in the tool schema."*
