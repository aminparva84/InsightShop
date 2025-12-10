# Environment Variables Setup Guide

## J.P. Morgan Payments API Configuration

The J.P. Morgan Payments API credentials are already configured as defaults in `config.py`, but for production use, you should set them as environment variables.

### Option 1: Create a `.env` file (Recommended)

Create a `.env` file in the project root directory with the following content:

```env
# J.P. Morgan Payments API Configuration
JPMORGAN_ACCESS_TOKEN_URL=https://id.payments.jpmorgan.com/am/oauth2/alpha/access_token
JPMORGAN_CLIENT_ID=92848822-381a-45ef-a20e-208dcf9efbed
JPMORGAN_CLIENT_SECRET=-0oVQVFeiXDW_0SQtaALMH62WVOiWF0Tw_QQV07qMai-oTs-aME5HSWfO9YQeh4tRabRa92eAdQfH4fdnzspsw
JPMORGAN_API_BASE_URL=https://api-mock.payments.jpmorgan.com/api/v2
JPMORGAN_MERCHANT_ID=998482157630
JPMORGAN_SCOPE=jpm:payments:sandbox
```

### Option 2: Set Environment Variables Directly

**Windows (PowerShell):**
```powershell
$env:JPMORGAN_CLIENT_ID="92848822-381a-45ef-a20e-208dcf9efbed"
$env:JPMORGAN_CLIENT_SECRET="-0oVQVFeiXDW_0SQtaALMH62WVOiWF0Tw_QQV07qMai-oTs-aME5HSWfO9YQeh4tRabRa92eAdQfH4fdnzspsw"
```

**Windows (Command Prompt):**
```cmd
set JPMORGAN_CLIENT_ID=92848822-381a-45ef-a20e-208dcf9efbed
set JPMORGAN_CLIENT_SECRET=-0oVQVFeiXDW_0SQtaALMH62WVOiWF0Tw_QQV07qMai-oTs-aME5HSWfO9YQeh4tRabRa92eAdQfH4fdnzspsw
```

**Linux/Mac:**
```bash
export JPMORGAN_CLIENT_ID="92848822-381a-45ef-a20e-208dcf9efbed"
export JPMORGAN_CLIENT_SECRET="-0oVQVFeiXDW_0SQtaALMH62WVOiWF0Tw_QQV07qMai-oTs-aME5HSWfO9YQeh4tRabRa92eAdQfH4fdnzspsw"
```

### Current Status

✅ **The credentials are already set as defaults in `config.py`**, so the integration will work without creating a `.env` file. However, for production:

1. **Security**: Never commit credentials to version control
2. **Flexibility**: Environment variables allow easy switching between sandbox and production
3. **Best Practice**: Use environment variables for all sensitive configuration

### Production Configuration

When moving to production, update these values:

```env
JPMORGAN_API_BASE_URL=https://api.payments.jpmorgan.com/api/v2
JPMORGAN_SCOPE=jpm:payments:production
JPMORGAN_MERCHANT_ID=your_production_merchant_id
JPMORGAN_CLIENT_ID=your_production_client_id
JPMORGAN_CLIENT_SECRET=your_production_client_secret
```

### Verification

To verify your environment variables are set correctly, run:

```bash
python scripts/test_jpmorgan_integration.py
```

This will test the OAuth2 token retrieval and payment creation with your configured credentials.


