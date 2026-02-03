# Sale System Implementation

## Overview

A comprehensive sale and discount system that integrates with seasonal events, holidays, and provides admin management capabilities.

## Features

### 1. Sale Model (`models/sale.py`)
- **Sale Management**: Create, update, and delete sales
- **Discount Percentage**: Set discount (0-100%)
- **Date Range**: Start and end dates for sales
- **Product Filters**: Filter sales by category, color, clothing_type, fabric, occasion, age_group
- **Event Association**: Link sales to holidays/events
- **Auto-activation**: Option to auto-activate based on event dates

### 2. Product Integration
- Products automatically calculate sale prices
- `get_sale_price()` method finds best applicable discount
- Products return both `original_price` and `price` (sale price if on sale)
- `on_sale` flag indicates if product is discounted

### 3. AI Chat Integration
- Shows current date in first message
- Celebrates active sales
- Mentions current holidays/events
- Highlights upcoming holidays

### 4. Admin Interface
- **GET `/api/admin/sales`**: List all sales
- **POST `/api/admin/sales`**: Create new sale
- **PUT `/api/admin/sales/<id>`**: Update sale
- **DELETE `/api/admin/sales/<id>`**: Delete sale
- **GET `/api/admin/sales/events`**: Get upcoming holidays/events for sale creation

### 5. Public API
- **GET `/api/sales/active`**: Get currently active sales
- **GET `/api/sales/upcoming`**: Get upcoming sales (next 30 days)
- **GET `/api/sales/current-context`**: Get current date, active sales, holidays, events

### 6. UI Display
- Product cards show original price with strikethrough
- Sale price displayed in red
- Discount badge shows percentage off
- Styling: `.original-price`, `.sale-price`, `.discount-badge`

## Database Schema

### Sales Table
```sql
CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sale_type VARCHAR(50) NOT NULL DEFAULT 'general',
    event_name VARCHAR(100),
    discount_percentage NUMERIC(5, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    product_filters TEXT,  -- JSON
    is_active BOOLEAN DEFAULT TRUE,
    auto_activate BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    updated_at DATETIME
);
```

## Usage Examples

### Creating a Sale via Admin API

```json
POST /api/admin/sales
{
  "name": "Valentine's Day Sale",
  "description": "Romantic pieces for your special someone",
  "sale_type": "holiday",
  "event_name": "valentines_day",
  "discount_percentage": 25.0,
  "start_date": "2024-02-10",
  "end_date": "2024-02-15",
  "product_filters": {
    "category": "women",
    "occasion": "date_night"
  },
  "is_active": true,
  "auto_activate": false
}
```

### Product Response with Sale

```json
{
  "id": 123,
  "name": "Red Dress",
  "price": 37.50,  // Sale price
  "original_price": 50.00,  // Original price
  "on_sale": true,
  "discount_percentage": 25.0,
  "sale": {
    "id": 1,
    "name": "Valentine's Day Sale",
    "discount_percentage": 25.0
  }
}
```

## AI Chat First Message Example

**Without Sales:**
> "Hi! I'm your AI shopping assistant. Today is January 15, 2024. How can I help you find the perfect clothes today?"

**With Active Sales:**
> "Hi! I'm your AI shopping assistant. Today is February 12, 2024. 🎉 Great news! We have 1 special sale running right now! Valentine's Day Sale - 25% off! Valentine's Day is coming up in 2 days! How can I help you find the perfect clothes today?"

## Admin Workflow

1. **View Events**: GET `/api/admin/sales/events` to see upcoming holidays
2. **Create Sale**: POST `/api/admin/sales` with event details
3. **Set Discount**: Choose percentage (e.g., 25% off)
4. **Set Filters**: Optionally filter by category, color, etc.
5. **Set Dates**: Choose start and end dates
6. **Activate**: Set `is_active: true` to enable sale

## Product Display

### Before Sale
```
$50.00
```

### During Sale
```
$50.00  $37.50  -25%
```
(Original price with strikethrough, sale price in red, discount badge)

## Integration Points

1. **Product Model**: `get_sale_price()` method
2. **Product API**: Returns sale information in `to_dict()`
3. **AI Chat**: Fetches sales context on load
4. **Product Cards**: Display sale prices with styling
5. **Cart**: Uses sale prices when adding to cart
6. **Orders**: Stores original price at time of order

## Future Enhancements

- Sale categories (site-wide, category-specific, product-specific)
- Stackable discounts
- Coupon codes
- Flash sales with countdown timers
- Email notifications for sales
- Sale analytics and reporting

