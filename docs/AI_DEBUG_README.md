# AI Debug CSV (InsightShop)

The file `ai_debug.csv` is a reference log for testing and debugging the InsightShop AI assistant. **Every user message results in one new row** in `ai_debug.csv` (success, error, or validation failure). It uses the same format as typical AI debug exports: **message**, **response**, **action_json**, **error**.

## Columns

| Column        | Description |
|---------------|-------------|
| **message**   | User input (what the user typed or said). |
| **response**  | Assistant reply shown to the user. |
| **action_json** | **Canonical JSON for every message:** `{"action": "STRING", "parameters": {}, "message": "STRING"}`. See Canonical action format below. |
| **error**     | Empty when successful; filled with error message or stack trace when the request failed. |

## Canonical action format (every message)

Every row’s **action_json** is normalized to this structure:

```json
{
  "action": "NONE | SEARCH_PRODUCTS | ADD_TO_CART | REMOVE_FROM_CART | UPDATE_CART_ITEM | CLEAR_CART | ADD_TO_WISHLIST | REMOVE_FROM_WISHLIST | VIEW_CART | VIEW_WISHLIST | REDIRECT | COMPARE_PRODUCTS",
  "parameters": {},
  "message": "Natural language response shown to the user."
}
```

- **action**: Required. One of the values above; use `NONE` when no backend action is required.
- **parameters**: Required; can be empty `{}`. Structured data for the action (e.g. `product_id`, `quantity`, `category`, `color`, `max_price`, `destination`).
- **message**: Required. The reply text displayed to the user.

The backend always writes this canonical form to **action_json** so that every message is logged in a consistent, machine-readable way.

## Use cases covered

The rows are aligned with InsightShop’s real flows:

### 1. Product search (tool: `search_products`)

- **By query:** e.g. “show me blue jackets”, “show women’s dresses”, “I need a jacket for winter”.
- **By category:** men, women, kids (e.g. “find men’s shirts under $50”, “show me kids clothing”).
- **By filters:** `max_price`, `size`, `sort_by` (relevance, price_low, price_high, rating).
- **On sale:** “what’s on sale?”, “list products on sale”, “show deals”.

### 2. Cart actions (agent: `add_item`, `remove_item`, `show_cart`, `clear_cart`)

- **Add:** by `product_id` (“add product 5 to cart”), or by `color` + `clothing_type` + optional `size` and `quantity` (“add 2 white shirts to my cart”, “add 1 navy blazer size M”).
- **Remove:** by `product_id` or by color/clothing_type, with optional `quantity` (“remove one black shirt”, “remove 2 white shirts”, “remove the blue jacket”).
- **Show cart:** “show my cart”, “show cart”, “show my cart again”.
- **Clear cart:** “clear cart”, “empty my cart”, “clear my shopping cart”.

### 3. General chat / info (`action: none`)

- **Policies:** return policy, shipping times, international (e.g. Canada).
- **Brand and support:** “tell me about your brand”, “where is the contact page?”.
- **Greetings and open-ended:** “hi”.
- **Follow-up without action:** “how much are they?” (prices of last search), “what sizes do you have?”.

### 4. Compare products (tool: `compare_products`)

- “compare product 1 and 2” → compare view with product IDs.

### 5. Edge cases and errors

- **Ambiguous add:** “add shirts to cart” with no color/type → assistant asks for clarification (no action or `none`).
- **Product not found:** “add product 99 to cart” → failure message; **error** column can note “Product not found or inactive”.
- **API/rate limit:** example row where **response** is an error message and **error** contains the raw exception (e.g. rate limit).

## How to use

- **Regression testing:** Replay **message** against the live AI endpoint and compare **response** and **action_json** (and **error** when present).
- **Documentation:** Shows expected (message → action/tool) behavior for product search, cart, and general chat.
- **Debugging:** When a user report matches a row, use **action_json** and **error** to see intended action and failure reason.

## Related docs

- **AI behavior and context:** `AI_ASSISTANT_BEHAVIOR.md`
- **Tools and permissions:** `mcp/insight_shop_tools.json`, `mcp/tools_registry.py`
- **Cart/agent actions:** `utils/agent_executor.py` (`ALLOWED_ACTIONS`, `execute_action`)
- **Search and tools:** `utils/tool_executor.py` (`_tool_search_products`), `utils/vector_db.py`

## API: `message_json` (every message)

Every chat response includes a **message_json** object. It contains both legacy fields and the **canonical** triple:

| Field        | Type    | Description |
|--------------|---------|-------------|
| **permission** | boolean | Whether the user/session was allowed to perform the action. |
| **action**     | string  | Internal action: `add_item`, `remove_item`, `show_cart`, `clear_cart`, `search_products`, `compare_products`, `none`, `redirect`. |
| **action_canonical** | string | Canonical action: `NONE`, `SEARCH_PRODUCTS`, `ADD_TO_CART`, `REMOVE_FROM_CART`, `VIEW_CART`, `CLEAR_CART`, `REDIRECT`, `COMPARE_PRODUCTS`, etc. |
| **parameters** | object | Structured data for the action (same as in **action_json** in ai_debug). |
| **message**    | string | Natural language response (same as **respond**). |
| **error**      | string \| null | Error message when status is `error` or `denied`; null on success. |
| **respond**    | string  | The reply text shown to the user. |
| **status**     | string  | `success`, `error`, or `denied`. |

- **CRUD actions** (`add_item`, `remove_item`, `show_cart`, `clear_cart`): the model uses backend tools (`execute_action`); permission is checked before execution.
- **Non-CRUD** (`search_products`, `compare_products`, `none`): the LLM answers itself (e.g. vector DB search, compare, or policy/greeting); no cart tool is called.
- **REDIRECT**: `parameters.destination` is one of `CART_PAGE`, `WISHLIST`, `CHECKOUT`, `MY_ORDERS`; the API returns `redirect_to` for the frontend.
