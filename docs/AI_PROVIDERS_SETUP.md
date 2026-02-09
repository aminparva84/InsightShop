# AI Assistant Setup (Direct API)

The AI chatbot uses **direct API keys** configured in **Admin → AI Assistant**. Bedrock is no longer used.

## Supported providers

| Provider | API key source | Example model IDs |
|----------|----------------|-------------------|
| **OpenAI** | [platform.openai.com](https://platform.openai.com/api-keys) | `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo` |
| **Google Gemini** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | `gemini-2.0-flash`, `gemini-1.5-pro` |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com/) | `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307` |
| **Custom** | Your own endpoint | Any; endpoint URL required |

## Admin panel

1. Go to **Admin** (superadmin only) → **AI Assistant**.
2. Choose **Provider** (OpenAI, Google Gemini, Anthropic, or Custom).
3. Enter **API key** (for Custom, enter the **API endpoint URL**).
4. Optionally set **Name** and **Model ID** (defaults are applied if left blank).
5. Check **Active** to show this model in the chatbot selector.
6. Click **Add model**. You can add multiple models and activate several at once.
7. Use **Test latency** to measure and store response time; **Activate** / **Deactivate** to show or hide the model in the chatbot.

## Chatbot

- Only **active** models appear in the chatbot.
- The user (or admin) selects a model from the **Model** dropdown in the chat header.
- The selected model is used for that conversation and is remembered (localStorage).

## Image analysis

Product image upload and “analyze image” use the same active config. Vision is supported for:

- **OpenAI** (e.g. `gpt-4o`, `gpt-4o-mini` with image)
- **Gemini** (e.g. `gemini-2.0-flash`)
- **Anthropic** (e.g. `claude-3-5-sonnet-20241022`)

If the active model does not support vision, a text-only fallback is used.
