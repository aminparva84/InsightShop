# Environment Variables Setup Guide

## AWS Credentials (S3, SES, Secrets Manager, Polly)

The app uses AWS for backups (S3), email (SES), optional secrets (Secrets Manager), and text-to-speech (Polly). Credentials are read from the environment and **must not be committed** to git.

### Set AWS credentials in `.env`

Add to your `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
```

Or run the helper script (one-time, from project root):

```bash
python scripts/set_aws_env.py YOUR_ACCESS_KEY_ID YOUR_SECRET_ACCESS_KEY
```

### Verify connection

```bash
python scripts/verify_aws_connection.py
```

You should see your AWS account ID and ARN. If you see errors, check that the IAM user has at least `sts:GetCallerIdentity` (and S3/SES/Polly permissions as needed).

### Security

- **Never commit `.env`** — it is listed in `.gitignore`.
- **Rotate keys** if they were ever shared (e.g. in chat or email). In AWS Console: IAM → Users → Security credentials → Create access key (then delete the old one).
- **Production (App Runner/ECS)**: Prefer IAM roles so no long-lived keys are stored; use Secrets Manager for other secrets.

---

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


