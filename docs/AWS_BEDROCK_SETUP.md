# AWS Bedrock Setup Guide

## Current Implementation

The AI agent uses **AWS Bedrock** with Claude (Anthropic) as the LLM. The system is designed to work with Bedrock, but has a graceful fallback if Bedrock is not configured.

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

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# Bedrock Model ID
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

Or set environment variables:

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 4. Verify Setup

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

