# Sale System Automation Guide

## Overview

The sale system is now fully automated and functional. All components are implemented and working:

1. ✅ **Sale Price Calculation** - Products automatically calculate sale prices
2. ✅ **Cart Integration** - Cart uses sale prices when calculating totals
3. ✅ **Order Integration** - Orders store sale prices at time of purchase
4. ✅ **UI Display** - Product cards and detail pages show sale prices with strikethrough
5. ✅ **Automation System** - Sales can be auto-activated based on dates

## How It Works

### 1. Sale Price Calculation

When a product is queried:
- `Product.get_sale_price()` checks all active sales
- Finds the best discount that applies to the product
- Returns sale price, original price, and discount percentage
- `Product.to_dict()` includes `on_sale`, `price` (sale price), `original_price`, and `discount_percentage`

### 2. Cart Integration

- Cart uses `product.to_dict()` which includes sale prices
- Cart totals are calculated using sale prices
- Both authenticated and guest carts support sale prices

### 3. Order Integration

- Orders use sale prices when creating orders
- Order items store the price paid (sale price if applicable)
- This ensures customers get the sale price even if sale ends after order

### 4. UI Display

- **Product Cards**: Show original price (strikethrough), sale price (red), and discount badge
- **Product Detail Pages**: Same display format
- CSS classes: `.original-price`, `.sale-price`, `.discount-badge`

## Automation Setup

### Option 1: Admin Panel Button (Recommended)

The easiest way to run sale automation is through the admin panel:

1. Go to `/admin` (must be logged in as admin)
2. Click "Sales Management" tab
3. Click the **"🔄 Run Sale Automation"** button
4. Confirm the action
5. The system will:
   - Activate sales based on their start dates
   - Sync holiday sales (create/update Cyber Monday, Thanksgiving, etc.)
   - Show results of what was activated/created/updated

This is perfect for manual control and testing.

### Option 2: Scheduled Task Endpoint

The system includes automation endpoints that can be called by cron jobs or scheduled tasks:

**Endpoint**: `POST /api/sale-automation/run`

**Authorization**: Bearer token (set `AUTOMATION_SECRET` environment variable)

**Example cron job** (runs daily at 2 AM):
```bash
0 2 * * * curl -X POST http://localhost:5000/api/sale-automation/run \
  -H "Authorization: Bearer YOUR_AUTOMATION_SECRET"
```

### Option 3: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `curl.exe`
6. Arguments: `-X POST http://localhost:5000/api/sale-automation/run -H "Authorization: Bearer YOUR_AUTOMATION_SECRET"`

### Option 4: Manual Activation

Sales can be manually activated/deactivated in the admin panel:
- Go to `/admin`
- Click "Sales Management" tab
- Use "Activate" or "Deactivate" buttons

## Automation Features

### Auto-Activation

Sales with `auto_activate=True` will automatically activate when:
- `start_date <= today`
- Sale is currently inactive (`is_active=False`)

### Holiday Sync

The automation system can automatically create/update holiday sales:
- **Cyber Monday**: 45% off, auto-created within 7 days of Cyber Monday
- **Thanksgiving**: 40% off, auto-created within 7 days of Thanksgiving

### Manual Control

Admins can:
- Manually activate/deactivate any sale
- Override automation by setting `is_active` flag
- Create custom sales with specific dates and discounts

## Testing

Run the test script to verify everything is working:

```bash
python scripts/test_sale_system.py
```

This will:
1. List all sales in the database
2. Show active sales
3. Test sale price calculation on products
4. Verify product.to_dict() includes sale information
5. Test sale matching logic

## API Endpoints

### Public Endpoints

- `GET /api/sales/active` - Get currently active sales
- `GET /api/sales/upcoming` - Get upcoming sales
- `GET /api/sales/current-context` - Get current date, active sales, holidays

### Admin Endpoints

- `GET /api/admin/sales` - List all sales
- `POST /api/admin/sales` - Create new sale
- `PUT /api/admin/sales/<id>` - Update sale
- `DELETE /api/admin/sales/<id>` - Delete sale
- `GET /api/admin/sales/events` - Get upcoming holidays/events
- `POST /api/admin/sales/run-automation` - Run sale automation (admin only)

### Automation Endpoints

- `POST /api/sale-automation/run` - Run all automation tasks
- `POST /api/sale-automation/activate` - Activate sales based on dates
- `POST /api/sale-automation/sync-holidays` - Sync holiday sales

## Environment Variables

Set these in your `.env` file or environment:

```bash
AUTOMATION_SECRET=your-secret-key-here  # For automation endpoint security
```

## Current Status

✅ **Cyber Monday Sale**: Active with 45% discount
✅ **Sale Price Calculation**: Working correctly
✅ **Cart Integration**: Using sale prices
✅ **Order Integration**: Storing sale prices
✅ **UI Display**: Showing sale prices correctly
✅ **Automation System**: Ready for scheduled tasks

## Next Steps

1. ✅ **Use the Admin Panel Button** - Click "🔄 Run Sale Automation" in the admin panel to manually trigger automation
2. (Optional) Set up a cron job or scheduled task to call `/api/sale-automation/run` daily for automatic execution
3. (Optional) Set `AUTOMATION_SECRET` environment variable for security (if using scheduled tasks)
4. Monitor sales in the admin panel
5. Create additional sales as needed

