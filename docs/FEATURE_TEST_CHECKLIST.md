# InsightShop Feature List & Test Checklist

**Excluded from this list:** AI Assistant (chat, AI search, AI filter) — not functional yet.

**Last API test run:** Backend and frontend started; API tests run via PowerShell.

---

## 1. Public / Guest

| # | Feature | Description | Route / API | Test |
|---|--------|-------------|-------------|------|
| 1.1 | **Home** | Landing page | `/` | Manual (UI) |
| 1.2 | **Product catalog** | List products, pagination | `/products`, `GET /api/products` | Pass |
| 1.3 | **Product filters** | Category, color, size, fabric, season, price, search | `GET /api/products?...` | Pass (APIs) |
| 1.4 | **Product detail** | Single product, variants (color/size), add to cart | `/products/:id`, `GET /api/products/:id` | Pass |
| 1.5 | **Product reviews** | View and submit reviews (submit may require auth) | `GET/POST /api/products/:id/reviews` | Pass (GET) |
| 1.6 | **Compare products** | Compare 2+ products (uses `/api/ai/compare` — no LLM) | `/compare?ids=1,2,3` | Pass |
| 1.7 | **Cart** | View cart, add/update/remove items, clear | `/cart`, `GET/POST/PUT/DELETE /api/cart` | Pass (add works for products with stock) |
| 1.8 | **Cart suggestions** | Product suggestions for cart | `GET /api/cart/suggestions` | Pass |
| 1.9 | **Cart matching pairs** | Matching outfit pairs | `GET /api/cart/matching-pairs` | Pass |
| 1.10 | **Login** | Email/password login | `/login`, `POST /api/auth/login` | Pass |
| 1.11 | **Register** | New account | `/register`, `POST /api/auth/register` | Pass |
| 1.12 | **Email verification** | Verify email after register | `/activation`, `POST /api/auth/verify` | Manual |
| 1.13 | **Health check** | API health | `GET /api/health` | Pass |

---

## 2. Authenticated Member

| # | Feature | Description | Route / API | Test |
|---|--------|-------------|-------------|------|
| 2.1 | **Members dashboard** | My account, dashboard stats | `/members`, `GET /api/members/dashboard` | Pass |
| 2.2 | **Member orders** | Order history | `GET /api/members/orders` | Pass |
| 2.3 | **Member payments** | Payment history | `GET /api/members/payments` | Pass |
| 2.4 | **Checkout** | Shipping, payment (Stripe / JPMorgan), place order | `/checkout`, `POST /api/shipping/rates`, etc. | Shipping Pass; payment Skip (external) |
| 2.5 | **Order confirmation** | Post-checkout confirmation | `/order-confirmation` | Manual after checkout |
| 2.6 | **Order details** | Single order | `GET /api/orders/:id` | Pass (with auth) |
| 2.7 | **Returns** | Initiate return, get return status | `POST /api/returns/initiate`, `GET /api/returns/:id` | Pass (endpoint validates; 400 for invalid order) |

---

## 3. Admin (Superadmin only)

| # | Feature | Description | Route / API | Test |
|---|--------|-------------|-------------|------|
| 3.1 | **Admin dashboard** | Stats, overview | `/admin` (tab: dashboard) | Pass (statistics API) |
| 3.2 | **Fashion KB** | Fashion knowledge base (colors, fabrics, etc.) | `GET/POST /api/admin/fashion-kb` | Pass |
| 3.3 | **User management** | List users, user details, toggle admin, delete, reset password | `GET /api/admin/users`, etc. | Pass (list) |
| 3.4 | **Product management** | List, create, edit, delete products | `GET/POST/PUT/DELETE /api/admin/products` | Pass (list) |
| 3.5 | **Order management** | List orders, order detail, update status | `GET /api/admin/orders`, `PUT .../status` | Pass (list) |
| 3.6 | **Sales** | List/create/edit/delete sales, events, run automation | `GET/POST/PUT/DELETE /api/admin/sales`, etc. | Pass (list, events) |
| 3.7 | **Payment logs** | View payment logs | `GET /api/admin/payment-logs` | Pass |
| 3.8 | **Carts** | List carts, user cart, clear cart | `GET /api/admin/carts`, etc. | Pass |
| 3.9 | **Reviews** | List reviews, delete review | `GET /api/admin/reviews`, `DELETE .../reviews/:id` | Pass (list) |
| 3.10 | **Statistics** | Dashboard statistics | `GET /api/admin/statistics` | Pass |

---

## 4. Supporting APIs (used by above)

| # | Feature | Description | API | Test |
|---|--------|-------------|-----|------|
| 4.1 | **Product filters metadata** | Categories, colors, sizes, fabrics, seasons, price range | `GET /api/products/categories`, `/colors`, `/sizes`, etc. | Pass |
| 4.2 | **Product search** | Semantic/search | `POST /api/products/search` | Pass |
| 4.3 | **Active/upcoming sales** | For banner/promos | `GET /api/sales/active`, `GET /api/sales/upcoming` | Pass |
| 4.4 | **Shipping rates** | Calculate shipping (body: `destination.city`, `destination.state`, `destination.zip`) | `POST /api/shipping/rates` | Pass |
| 4.5 | **Images** | Product images | `GET /api/images/:filename`, `GET /api/images/generated/:filename` | Manual if needed |

---

## Notes from testing

- **Cart add:** Returns 400 "Insufficient stock" when product has no stock (e.g. product id 1). Use a product with `stock_quantity > 0` (e.g. id 2).
- **Shipping:** Request body must use `destination: { city, state, zip }`, not `address`.
- **Payments:** Stripe/JPMorgan not exercised (external; mark as Skip in dev).

---

## Test key

- **Pass**: Feature works as expected (API or manual).
- **Fail**: Error, wrong behavior, or missing data.
- **Skip**: Not tested (e.g. external payment in dev).
- **Manual**: Prefer a quick UI check in the browser.
