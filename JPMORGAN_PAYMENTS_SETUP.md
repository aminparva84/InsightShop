# J.P. Morgan Payments API Integration

This document describes how to set up and use the J.P. Morgan Payments API integration in InsightShop.

## Configuration

Add the following environment variables to your `.env` file:

```env
# J.P. Morgan Payments API Configuration
JPMORGAN_ACCESS_TOKEN_URL=https://id.payments.jpmorgan.com/am/oauth2/alpha/access_token
JPMORGAN_CLIENT_ID=92848822-381a-45ef-a20e-208dcf9efbed
JPMORGAN_CLIENT_SECRET=-0oVQVFeiXDW_0SQtaALMH62WVOiWF0Tw_QQV07qMai-oTs-aME5HSWfO9YQeh4tRabRa92eAdQfH4fdnzspsw
JPMORGAN_API_BASE_URL=https://api-mock.payments.jpmorgan.com/api/v2
JPMORGAN_MERCHANT_ID=998482157630
JPMORGAN_SCOPE=jpm:payments:sandbox
```

## API Endpoints

### 1. Get Access Token (Testing)

**Endpoint:** `GET /api/payments/jpmorgan/token`

**Description:** Retrieves a fresh OAuth2 access token from J.P. Morgan Payments API. Useful for testing and debugging.

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJraWQiOiJJR04...",
  "message": "Token retrieved successfully"
}
```

### 2. Create Payment

**Endpoint:** `POST /api/payments/jpmorgan/create-payment`

**Description:** Creates a payment using J.P. Morgan Payments API.

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <jwt_token>` (optional, for authenticated users)

**Request Body:**
```json
{
  "order_id": 123,
  "card_number": "4012000033330026",
  "expiry_month": 5,
  "expiry_year": 2027,
  "capture_method": "NOW",
  "merchant_company_name": "InsightShop",
  "merchant_product_name": "InsightShop Application",
  "merchant_version": "1.0.0",
  "merchant_category_code": "4899",
  "is_bill_payment": true,
  "initiator_type": "CARDHOLDER",
  "account_on_file": "NOT_STORED",
  "is_amount_final": true
}
```

**Response (Success):**
```json
{
  "message": "Payment processed",
  "payment": {
    "id": 1,
    "order_id": 123,
    "payment_method": "jpmorgan",
    "payment_intent_id": "9f186d77-cb1b-4a9f-bb44-b5be91b891ac",
    "amount": 12.34,
    "currency": "USD",
    "status": "completed",
    "transaction_id": "9f186d77-cb1b-4a9f-bb44-b5be91b891ac",
    "created_at": "2023-09-18T18:04:26.898Z",
    "updated_at": "2023-09-18T18:04:26.898Z"
  },
  "jpmorgan_response": {
    "transaction_id": "9f186d77-cb1b-4a9f-bb44-b5be91b891ac",
    "response_status": "SUCCESS",
    "response_code": "APPROVED",
    "response_message": "Transaction approved by Issuer",
    "full_response": { ... }
  }
}
```

### 3. Get Payment Status

**Endpoint:** `GET /api/payments/jpmorgan/payment-status/<transaction_id>`

**Description:** Retrieves the current status of a payment from J.P. Morgan Payments API.

**Headers:**
- `Authorization: Bearer <jwt_token>` (optional, for authenticated users)

**Response:**
```json
{
  "payment": {
    "id": 1,
    "order_id": 123,
    "payment_method": "jpmorgan",
    "status": "completed",
    "transaction_id": "9f186d77-cb1b-4a9f-bb44-b5be91b891ac",
    ...
  },
  "jpmorgan_status": {
    "transactionId": "9f186d77-cb1b-4a9f-bb44-b5be91b891ac",
    "responseStatus": "SUCCESS",
    "responseCode": "APPROVED",
    ...
  }
}
```

## Usage Example

### Using cURL

1. **Get Access Token:**
```bash
curl -X GET http://localhost:5000/api/payments/jpmorgan/token
```

2. **Create Payment:**
```bash
curl -X POST http://localhost:5000/api/payments/jpmorgan/create-payment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{
    "order_id": 123,
    "card_number": "4012000033330026",
    "expiry_month": 5,
    "expiry_year": 2027
  }'
```

3. **Check Payment Status:**
```bash
curl -X GET http://localhost:5000/api/payments/jpmorgan/payment-status/9f186d77-cb1b-4a9f-bb44-b5be91b891ac \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Using Python

```python
import requests

# Create payment
response = requests.post(
    'http://localhost:5000/api/payments/jpmorgan/create-payment',
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer <your_jwt_token>'
    },
    json={
        'order_id': 123,
        'card_number': '4012000033330026',
        'expiry_month': 5,
        'expiry_year': 2027
    }
)

result = response.json()
transaction_id = result['jpmorgan_response']['transaction_id']

# Check payment status
status_response = requests.get(
    f'http://localhost:5000/api/payments/jpmorgan/payment-status/{transaction_id}',
    headers={'Authorization': 'Bearer <your_jwt_token>'}
)
```

## Implementation Details

### OAuth2 Token Management

The integration automatically handles OAuth2 token retrieval and caching:
- Tokens are cached to avoid unnecessary API calls
- Tokens are automatically refreshed when they expire
- Token expiration is tracked with a 60-second safety buffer

### Payment Processing Flow

1. Client sends payment request with order ID and card details
2. Backend retrieves order and validates it
3. Backend gets OAuth2 access token (cached if available)
4. Backend creates payment request to J.P. Morgan Payments API
5. Backend stores payment record in database
6. Backend updates order status based on payment response

### Error Handling

The integration handles various error scenarios:
- Invalid credentials
- Network errors
- API errors from J.P. Morgan Payments
- Invalid order or payment states
- Authentication/authorization errors

## Security Notes

1. **Never commit credentials to version control** - Use environment variables
2. **Use HTTPS in production** - All API calls should be over HTTPS
3. **Validate card data on frontend** - Never send raw card data without validation
4. **Store minimal card data** - Only store what's necessary (masked numbers, last 4 digits)
5. **Use PCI-compliant practices** - Follow PCI DSS guidelines for handling card data

## Testing

The integration uses the J.P. Morgan Payments sandbox environment by default. Test card numbers:

- **Success:** `4012000033330026`
- **Decline:** Various test cards available in J.P. Morgan Payments documentation

## Production Considerations

1. Update `JPMORGAN_API_BASE_URL` to production endpoint
2. Update `JPMORGAN_SCOPE` to production scope
3. Ensure proper error logging and monitoring
4. Implement webhook handling for payment status updates
5. Add retry logic for transient failures
6. Implement rate limiting for API calls


