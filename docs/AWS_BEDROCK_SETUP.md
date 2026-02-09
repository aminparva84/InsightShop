# AWS Bedrock — Removed

**AWS Bedrock is no longer used** for the AI assistant in InsightShop.

The project uses **simple API keys** for AI providers configured in **Admin → AI Assistant**:

- **OpenAI** — API key from [platform.openai.com](https://platform.openai.com/api-keys)
- **Google Gemini** — API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Anthropic** — API key from [console.anthropic.com](https://console.anthropic.com/)

See [AI_PROVIDERS_SETUP.md](AI_PROVIDERS_SETUP.md) for setup. AWS credentials are still used for Polly (TTS), S3, SES, and Secrets Manager — see [AWS_CONNECTION.md](AWS_CONNECTION.md).
