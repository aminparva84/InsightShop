# Where Access Key & Secret Key Come From — Pipeline and Docker

This doc explains how **AWS access key / secret key** and the **admin-panel API key** fit together, and how the rest of the pipeline works when running in **Docker**.

---

## 1. Two places credentials can come from

| Source | What it is | Used for |
|-------|------------|----------|
| **Environment (Config)** | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` from env (e.g. `.env`, Docker `-e` or `--env-file`, or injected by App Runner from Secrets Manager). | AWS usage app‑wide: Polly, SES, S3 scripts, Secrets Manager fetch. |
| **Admin panel (AI Assistant)** | The **API key** and optional **model ID** you set in **Admin → AI Assistant** for OpenAI, Gemini, or Anthropic. | The **AI chat/assistant pipeline** only; all three providers use simple API keys. |

So:

- **Access key and secret key** (AWS IAM credentials) come from **Environment** (Config) or **IAM role** when running on AWS. They are used for Polly, SES, S3, and Secrets Manager — not for the AI assistant.
- The **AI assistant** uses **simple API keys** from Admin → AI Assistant (OpenAI, Google Gemini, Anthropic). See [AI_PROVIDERS_SETUP.md](AI_PROVIDERS_SETUP.md). AWS Bedrock has been removed.

---

## 2. How the pipeline uses them (by feature)

### AI Assistant (chat, vision, etc.) — `routes/ai_agent.py`

- Uses **Admin → AI Assistant** config only: API key and optional model ID for the selected provider (OpenAI, Gemini, or Anthropic). No AWS access/secret key for the AI assistant.

### Other AWS usage (Polly, SES, S3, Secrets Manager)

- **Polly (TTS)**  
  - Built at startup from **Config**: if `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set, those are used; otherwise boto3 uses the **default credential chain** (env vars, then IAM role, etc.).

- **SES (email)**  
  - `utils/email.py` creates the client with only `region_name=Config.AWS_REGION`. So it uses the **default credential chain** (env or IAM).

- **S3 (backup/restore scripts)**  
  - Use **Config** keys if set; otherwise boto3 falls back to the default chain.

- **Secrets Manager (startup)**  
  - `utils/secrets_loader.load_into_env()` uses boto3 **without** explicit keys → **default credential chain** (env or IAM). So in Docker with an IAM role, the container can read the secret and set env vars (e.g. `JWT_SECRET`, or even `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` if you store them there).

So across the app:

- **Access key and secret key** = either from **env (Config)** or from **IAM** (when you don’t set them in env). Used for Polly, SES, S3, Secrets Manager.
- **Admin panel** = only for the **AI assistant**: simple API keys for OpenAI, Gemini, or Anthropic.

---

## 3. How Docker fits in (credentials and pipeline)

- **No secrets in the image**  
  The Dockerfile does **not** bake in any API or AWS keys. All credentials are provided at **runtime**.

- **Startup order in the container**
  1. Container starts → runs `app:app` (e.g. gunicorn).
  2. **Before** loading Flask/Config, `app.py` runs `load_into_env()`. If `AWS_SECRETS_INSIGHTSHOP` is set, the app calls Secrets Manager (using the **default credential chain**: env or IAM) and pushes secret key/values into `os.environ`.
  3. Then `Config` is loaded from `os.environ` (and `.env` if present). So `JWT_SECRET`, `SECRET_KEY`, and optionally `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` can come from the secret.
  4. When a user hits the AI assistant, the **active** AI Assistant config (from the DB) is used — API key and model from Admin for the selected provider (OpenAI, Gemini, or Anthropic).

- **Ways to supply credentials in Docker**

  | Scenario | How access/secret key are supplied | Admin panel role |
  |----------|-----------------------------------|-------------------|
  | **Docker on your machine** | `--env-file` or `-e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=...` for Polly/S3/SES. | Set API keys in Admin → AI Assistant for OpenAI, Gemini, or Anthropic. |
  | **Docker on AWS (App Runner / ECS)** | Prefer **IAM role** for the task/service. Optionally inject other secrets (e.g. `JWT_SECRET`) from Secrets Manager. | Same: set AI provider API keys in Admin. |
  | **Secrets Manager at startup** | Set env `AWS_SECRETS_INSIGHTSHOP=insightshop/production`. After `load_into_env()`, `Config` can get keys from the secret. | AI assistant still uses Admin → AI Assistant API keys. |

So in Docker:

- **AWS credentials** for Polly, SES, S3, Secrets Manager come from **environment** or **IAM**.
- The **AI assistant** uses **simple API keys** from Admin → AI Assistant (OpenAI, Gemini, Anthropic).

---

## 4. Short summary

- **Access key and secret key** = AWS IAM credentials for Polly, SES, S3, Secrets Manager. From **Environment** (Config) or **IAM role**.
- **AI assistant** = simple API keys in Admin → AI Assistant (OpenAI, Gemini, Anthropic). Bedrock has been removed.
- **Docker:** Env (or IAM) → `load_into_env()` (optional) → Config → app uses Config for AWS; AI chat uses active admin config (API key + model).
