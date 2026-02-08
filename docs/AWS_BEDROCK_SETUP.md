# AWS Bedrock Setup Guide

## Current Implementation

The AI agent uses **AWS Bedrock** with Claude (Anthropic) as the LLM. The system is designed to work with Bedrock, but has a graceful fallback if Bedrock is not configured.

**Bedrock does not use a single “API key”** like OpenAI or Gemini. It uses **AWS IAM credentials**: an **Access Key ID** and a **Secret Access Key**. You can provide them in either of two ways (see below).

## How It Works

1. **With Bedrock Configured**: The AI agent calls AWS Bedrock API to get responses from Claude
2. **Without Bedrock**: The system falls back to a simple response indicating Bedrock needs to be configured

## Setup Instructions

### 1. AWS Account Setup

1. Log in to your AWS Console
2. Navigate to **Amazon Bedrock** service
3. Request access to **Anthropic Claude** models (if not already enabled)
4. Go to **Model access** and enable:
   - `anthropic.claude-3-sonnet-20240229-v1:0` (or latest Claude 3 Sonnet)
   - Or `anthropic.claude-3-haiku-20240307-v1:0` for faster/cheaper responses

### 2. Create IAM User/Role

1. Go to **IAM** in AWS Console
2. Create a new user or use existing credentials
3. Attach policy: `AmazonBedrockFullAccess` (or create custom policy with Bedrock invoke permissions)
4. Create Access Key ID and Secret Access Key

### 3. Provide AWS Credentials (choose one)

You can provide AWS credentials in **either** of these ways:

#### Option A: Environment variables (recommended for local or Docker)

Create a `.env` file in the project root:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# Bedrock Model ID (optional; can also set in Admin → AI Assistant)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

Or set environment variables:

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

Then in **Admin → AI Assistant**, choose **AWS Bedrock** as the provider and **leave the “API key” field blank**. The app will use the credentials from `.env`.

#### Option B: Admin → AI Assistant (no .env needed)

1. Go to **Admin** (superadmin) → **AI Assistant**.
2. Set **Model** to **AWS Bedrock**.
3. In the **API key** column for the Bedrock row, enter your credentials in this exact format:  
   **`AccessKeyID:SecretAccessKey`** (one colon, no spaces).  
   Example: `AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
4. Click **Save**, then **Test**. If the test passes, the assistant will use Bedrock.

You can also set **Region** and **Model ID** for that provider in the backend (Admin PATCH API) if your UI exposes them.

### 4. Enable model access (required — fixes "Operation not allowed")

Even with valid IAM credentials, Bedrock returns **"ValidationException: Operation not allowed"** until you enable access to a foundation model:

1. In AWS Console go to **Amazon Bedrock**.
2. In the left menu click **Model access** (under "Bedrock configurations" or "Get started").
3. Click **Manage model access** or **Modify model access**.
4. Expand **Anthropic** and enable at least one model, for example:
   - **Claude 3 Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`) — fast, cheap, available in many regions including `us-east-1`.
   - **Claude 3.5 Sonnet** or **Claude Sonnet 4** — better quality.
5. Click **Save changes** / **Request model access** and wait until status is **Granted** (often within a few minutes).
6. Ensure your **region** in Admin → AI Assistant (or `AWS_REGION` in .env) matches a region where the model is available (e.g. `us-east-1` for Claude 3 Haiku).

After access is granted, the chatbot should work without changing credentials.

### 5. Verify Setup

The AI agent will automatically detect if Bedrock is configured. When you chat with the AI:
- **If configured**: You'll get intelligent, conversational responses from Claude
- **If not configured**: You'll see a message that Bedrock needs to be set up

## Current Status

The AI agent code is in `routes/ai_agent.py` and uses:
- `boto3` client for AWS Bedrock Runtime
- Claude 3 Sonnet model (configurable)
- Fashion knowledge base for enhanced responses
- Product database access for real-time information

## Testing

After setup, test by asking the AI:
- "Show me blue shirts"
- "What fabric is product #123 made from?"
- "Compare product 1, 2, 3"
- "What should I wear for a business meeting?"

If Bedrock is working, you'll get detailed, conversational responses with fashion advice.

## Note

The LLM is **NOT offline** - it requires AWS Bedrock API access. The system will work without Bedrock but with limited functionality (fallback mode).

