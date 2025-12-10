# Shipping API Setup Guide

This guide explains how to set up and use the FedEx and UPS shipping API integration for InsightShop.

## Overview

The shipping system provides real-time rate calculation from FedEx and UPS APIs. If the APIs are unavailable or not configured, the system falls back to default rates.

## Features

- ✅ **FedEx API Integration** - Real-time rate calculation
- ✅ **UPS API Integration** - Real-time rate calculation
- ✅ **Automatic Fallback** - Uses default rates if APIs are unavailable
- ✅ **Multiple Service Options** - Ground, Express, Overnight shipping
- ✅ **Frontend Integration** - Dynamic rate display in checkout

## API Endpoints

### 1. Calculate Shipping Rates

**Endpoint:** `POST /api/shipping/rates`

**Request Body:**
```json
{
  "destination": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "US"
  },
  "weight": 2.5,
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 6
  }
}
```

**Response:**
```json
{
  "fedex": [
    {
      "service": "FedEx Ground",
      "service_code": "FEDEX_GROUND",
      "carrier": "FedEx",
      "price": 8.50,
      "currency": "USD",
      "estimated_days": 5
    }
  ],
  "ups": [
    {
      "service": "UPS Ground",
      "service_code": "03",
      "carrier": "UPS",
      "price": 7.25,
      "currency": "USD",
      "estimated_days": 5
    }
  ],
  "errors": []
}
```

### 2. Quick Shipping Rates

**Endpoint:** `POST /api/shipping/rates/quick`

**Request Body:**
```json
{
  "zip": "10001",
  "state": "NY",
  "country": "US"
}
```

**Response:**
```json
{
  "rates": [
    {
      "service": "UPS Ground",
      "carrier": "UPS",
      "price": 7.25,
      "estimated_days": 5
    }
  ],
  "errors": []
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

#### FedEx API Configuration

```env
# FedEx API Credentials (get from https://developer.fedex.com/)
FEDEX_API_KEY=your_fedex_api_key
FEDEX_SECRET_KEY=your_fedex_secret_key
FEDEX_ACCOUNT_NUMBER=your_fedex_account_number
FEDEX_METER_NUMBER=your_fedex_meter_number
FEDEX_USE_PRODUCTION=false  # Set to 'true' for production
```

#### UPS API Configuration

```env
# UPS API Credentials (get from https://developer.ups.com/)
UPS_API_KEY=your_ups_api_key
UPS_USERNAME=your_ups_username
UPS_PASSWORD=your_ups_password
UPS_ACCOUNT_NUMBER=your_ups_account_number
UPS_USE_PRODUCTION=false  # Set to 'true' for production
```

#### Shipping Origin Address

```env
# Your warehouse/store origin address
SHIPPING_ORIGIN_STREET=123 Main St
SHIPPING_ORIGIN_CITY=New York
SHIPPING_ORIGIN_STATE=NY
SHIPPING_ORIGIN_ZIP=10001
SHIPPING_ORIGIN_COUNTRY=US
```

## Getting API Credentials

### FedEx API Setup

1. Go to [FedEx Developer Portal](https://developer.fedex.com/)
2. Create an account or sign in
3. Create a new application
4. Get your API Key and Secret Key
5. Get your Account Number and Meter Number from your FedEx account

### UPS API Setup

1. Go to [UPS Developer Portal](https://developer.ups.com/)
2. Create an account or sign in
3. Create a new application
4. Get your API Key (Client ID)
5. Get your Username and Password from your UPS account
6. Get your Account Number from your UPS account

## Testing

### Test Mode (Sandbox)

By default, the system uses sandbox/test mode. Set these to `false`:
- `FEDEX_USE_PRODUCTION=false`
- `UPS_USE_PRODUCTION=false`

### Production Mode

When ready for production:
- Set `FEDEX_USE_PRODUCTION=true`
- Set `UPS_USE_PRODUCTION=true`
- Use production API credentials

## Fallback Behavior

If the APIs are not configured or unavailable, the system automatically falls back to default rates:

- **Ground Shipping:** $5.00
- **Express Shipping:** $15.00
- **Overnight Shipping:** $25.00

The system also maintains the existing "Free shipping over $50" logic as a fallback.

## Frontend Integration

The checkout page automatically:
1. Fetches shipping rates when ZIP code and state are entered
2. Displays available shipping options from FedEx and UPS
3. Allows users to select their preferred shipping method
4. Falls back to standard rates if APIs are unavailable

## Usage in Code

### Backend (Python)

```python
from utils.shipping import ShippingService

shipping_service = ShippingService()

rates = shipping_service.calculate_rates(
    destination={
        'street': '123 Main St',
        'city': 'New York',
        'state': 'NY',
        'zip': '10001',
        'country': 'US'
    },
    weight=2.5,
    dimensions={'length': 10, 'width': 8, 'height': 6}
)

print(rates['fedex'])
print(rates['ups'])
```

### Frontend (React)

```javascript
const response = await axios.post('/api/shipping/rates/quick', {
  zip: '10001',
  state: 'NY',
  country: 'US'
});

const rates = response.data.rates;
```

## Error Handling

The system handles errors gracefully:

1. **API Unavailable:** Falls back to default rates
2. **Invalid Credentials:** Logs error and uses fallback
3. **Network Issues:** Uses cached or default rates
4. **Invalid Address:** Returns error message to user

All errors are logged for debugging but don't break the checkout flow.

## Troubleshooting

### Rates Not Loading

1. Check API credentials in `.env` file
2. Verify API keys are valid
3. Check network connectivity
4. Review server logs for errors

### Incorrect Rates

1. Verify origin address is correct
2. Check package weight and dimensions
3. Ensure using correct API environment (sandbox vs production)

### API Errors

1. Check API documentation for changes
2. Verify account status with carrier
3. Ensure API keys have correct permissions

## Support

For issues with:
- **FedEx API:** Contact [FedEx Developer Support](https://developer.fedex.com/support)
- **UPS API:** Contact [UPS Developer Support](https://developer.ups.com/support)
- **Integration Issues:** Check server logs and error messages

## Notes

- The system uses REST APIs for both FedEx and UPS
- OAuth 2.0 authentication for FedEx
- Basic authentication for UPS
- All rates are in USD
- Weight is in pounds, dimensions in inches
- Estimated delivery days are approximate


