# AI Assistant Behavior & Context

This document describes how the InsightShop AI assistant is configured to provide **contextual awareness**, **accurate information**, and **user-level action execution** in line with the product requirements.

---

## 1. Context Awareness

### Website information (policies, pages, features)

The assistant receives a fixed **website context** in its system prompt, including:

- **Shipping**: Processing times (same/next business day), methods (Standard 5–7 days, expedited, express), domestic and international.
- **Returns**: 30-day window from delivery, eligibility (unworn, original condition, tags), how to start a return (Order History → select order → items and reason).
- **About**: Brand summary (timeless, quality clothing; men, women, kids; mission and values).
- **Contact**: How to reach support (/contact with name, email, optional order number, message).
- **Pages**: /about, /shipping, /returns, /contact.

The assistant is instructed to use this context to answer policy and info questions **accurately** and **not to invent** details.

### Product catalog

- In **standard chat** (`/api/ai/chat`): Product sample, search results, and filters are built from the catalog and passed to the LLM; responses use Product #ID, name, price.
- In **tool-capable chat** (`/api/ai/chat-with-tools`): The assistant can call `search_products` (and other tools); when it does, the backend attaches `suggested_products` and `suggested_product_ids` to the response so the frontend can show or navigate to results.

### User data (logged-in users only)

For **logged-in** users using `/api/ai/chat-with-tools`, the backend injects a short **user context** into the system prompt, for example:

- Number of items in **wishlist**
- Number of items in **cart**
- **Recent orders** summary (e.g. count and last order number + status)

The assistant is instructed to use this to personalize replies (e.g. “You have 3 items in your wishlist”) and to avoid asking for information we already have.

---

## 2. Core Behavior

- **Natural and conversational**: Tone is professional, friendly, and aligned with the brand.
- **Accurate answers**: Based on website context and product data; the assistant is told not to invent policies or product/order details.
- **Personalization**: When user context is present, the assistant can reference wishlist, cart, and order history.
- **Clarification**: If the request is unclear or incomplete, the assistant asks short follow-up questions.
- **Confirmation**: For critical or irreversible actions (e.g. clear cart, remove from wishlist), the assistant confirms before executing.
- **No hallucination**: Only perform and describe actions that are explicitly allowed; if something cannot be done or data is missing, say so and suggest alternatives when appropriate.

---

## 3. Action Execution (user-level only)

The assistant can perform **only** the user-level actions defined in the tools registry (see `mcp/insight_shop_tools.json` and `docs/InsightShop_User_Capabilities.xlsx`). **Superadmin/admin-only** capabilities are excluded for regular users.

Examples of **user** actions the assistant can execute (when the user is logged in and using tool-capable chat):

- **Auth**: Log in, log out (via tools; frontend may handle UI).
- **Search**: Search products (query, category, size, max price, sort).
- **Cart**: Add/remove items, show cart, clear cart.
- **Wishlist**: View wishlist, add to wishlist, remove from wishlist.
- **Orders**: Order status (by order ID + email), track shipment (by tracking number).
- **Compare**: Compare two or more products by ID.
- **Reviews**: Create a product review (rating + optional comment).
- **Checkout**: Proceed to checkout with shipping details (when the tool is used).

Admin-only tools (e.g. product create/update/delete, orders list, sales, carts, reviews management) are **only** available when the current user is an **admin/superadmin**; the backend enforces this on every tool call.

---

## 4. Which endpoint is used?

- **Guests** (not logged in): Use **`/api/ai/chat`**. No tool execution; conversation and product search only, with website context in the prompt.
- **Logged-in users**: Use **`/api/ai/chat-with-tools`**. Full user-level tool set plus website and user context. Admins get the same plus admin tools.

The frontend chooses the endpoint based on whether a user is present (`user ? '/api/ai/chat-with-tools' : '/api/ai/chat'`). All requests that require auth send the same auth header (e.g. Bearer token) used elsewhere in the app.

---

## 5. Action workflow

When performing an action, the assistant is expected to:

1. **Understand** the request (use conversation history and context).
2. **Validate** permissions (backend enforces user vs admin tools).
3. **Confirm** when appropriate (e.g. “Should I remove that from your wishlist?”).
4. **Execute** via the tool; the backend runs the tool and returns the result.
5. **Inform** the user in natural language (e.g. “Your item has been added to your wishlist.”).

The backend returns a clear `response` message and, for search, optional `suggested_products` / `suggested_product_ids` and `action: 'search_results'` so the UI can update or navigate.

---

## 6. Implementation notes

- **Website context**: `ASSISTANT_WEBSITE_CONTEXT` in `routes/ai_agent.py`.
- **User context**: `get_assistant_user_context(user)` in `routes/ai_agent.py` (wishlist count, cart count, recent orders summary).
- **System prompt**: `TOOLS_SYSTEM_PROMPT` in `routes/ai_agent.py` includes context-awareness, intent clarification, confirmation for critical actions, and “user-level only / do not hallucinate” rules.
- **Standard chat**: `ASSISTANT_WEBSITE_CONTEXT` is also injected into the main `/api/ai/chat` system prompt so guests get accurate policy/shipping/returns answers.
- **Tools**: User vs admin tools are defined in `mcp/insight_shop_tools.json` and filtered by `get_tools_for_llm(role)` in `mcp/tools_registry.py`; execution and permission checks are in `routes/ai_agent.py` and `utils/tool_executor.py`.

User capabilities (canonical list) are in `scripts/generate_user_capabilities_excel.py` and the generated `docs/InsightShop_User_Capabilities.xlsx`; the assistant must not perform actions outside that list for the current user type.
