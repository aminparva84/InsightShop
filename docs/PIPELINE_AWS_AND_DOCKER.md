# Where Access Key & Secret Key Come From — Pipeline and Docker

This doc explains how **AWS access key / secret key** and the **admin-panel API key** fit together, and how the rest of the pipeline works when running in **Docker**.

---

## 1. Two places credentials can come from

| Source | What it is | Used for |
|-------|------------|----------|
| **Environment (Config)** | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` from env (e.g. `.env`, Docker `-e` or `--env-file`, or injected by App Runner from Secrets Manager). | Default AWS usage app‑wide: Bedrock fallback, Polly, SES, S3 scripts, Secrets Manager fetch. |
| **Admin panel (AI Assistant)** | The **API key** and **region** (and optional `access_key:secret_key` for Bedrock) you set in **Admin → AI Assistant** for the **active** config. | Only the **AI chat/assistant pipeline** when the active config is Bedrock or OpenAI. |

So:

- **Access key and secret key** in the sense of “AWS IAM credentials” come from:
  1. **Environment** (Config) — used by the whole app (Bedrock fallback, Polly, SES, S3, secrets fetch).
  2. **Admin panel** — only for the **Bedrock** assistant: you can put `access_key:secret_key` in the single “API key” field, or leave it blank and use env (or IAM) instead.
- The **admin “API key”** is:
  - **OpenAI:** your OpenAI API key (not AWS).
  - **Bedrock:** either “leave blank to use env/IAM” or “`access_key:secret_key`” (or just the secret if the app uses Config for access key — see code).
  - **Custom:** optional auth key for your custom endpoint.

---

## 2. How to use the admin Bedrock field

In **Admin → AI Assistant**, choose **Provider: AWS Bedrock**. You’ll see:

| Field      | Required? | What to put |
|-----------|-----------|-------------|
| **Name**  | Yes       | A label, e.g. `Production Claude` or `Bedrock us-east-1`. |
| **Provider** | Yes   | `AWS Bedrock`. |
| **API key**   | No*   | See options below. |
| **Model ID**  | No    | Bedrock model id, e.g. `anthropic.claude-3-sonnet-20240229-v1:0` or `anthropic.claude-3-5-sonnet-20241022-v2:0`. Leave blank to use the app default from env. |
| **Region**    | No    | AWS region for Bedrock, e.g. `us-east-1`. Defaults to `us-east-1` if blank. |

\* You must supply credentials in one of these ways:

### Option A: Use IAM or environment (recommended on AWS)

- Leave **API key** **empty**.
- Ensure the app has AWS credentials from either:
  - **IAM role** (App Runner / ECS task role with Bedrock access), or  
  - **Environment:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_REGION`.

The pipeline will use those credentials for Bedrock. No need to store keys in the admin panel.

### Option B: Put both keys in the API key field

- In **API key**, enter a **single string** in the form:
  - `ACCESS_KEY_ID:SECRET_ACCESS_KEY`
- Example (fake values): `AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
- Use a real **Access key ID** and **Secret access key** from IAM (no spaces; one colon between them).

The pipeline uses only this config for Bedrock; it does not use `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` from the environment for the assistant.

### Option C: Secret key in admin, access key from environment

- In **API key**, enter **only** your AWS **Secret access key** (do **not** include a colon or the access key).
- Set **Environment:** `AWS_ACCESS_KEY_ID` (and optionally `AWS_SECRET_ACCESS_KEY`; the secret from the panel will override for Bedrock).

The pipeline uses the access key from Config and the secret from the admin field. This is less common; Option A or B is usually simpler.

### After saving

- Click **Add and set as active**. The new config becomes the active AI assistant.  
- The chatbot will use this Bedrock config (with the credentials you chose above) plus the **Model ID** and **Region** you set, or the app defaults when those are blank.

---

## 3. How the pipeline uses them (by feature)

### AI Assistant (chat, vision, etc.) — `routes/ai_agent.py`

- **Active config = OpenAI**  
  - Uses only **admin panel**: API key and model ID from the active AI Assistant config.  
  - No AWS access/secret key.

- **Active config = Bedrock**  
  Credentials are chosen in this order:
  1. If the admin “API key” is set and contains `:` → use it as `access_key:secret_key` for Bedrock only.
  2. Else if admin “API key” is empty and **Config** has `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` → use those for Bedrock.
  3. Else if admin “API key” is non‑empty (no `:`) → that value is used as the secret key; access key comes from Config (see `ai_agent.py`).
  - Region: active config’s **region** or `Config.AWS_REGION`.
  - So: **access key and secret key** for the Bedrock part of the pipeline come from **admin panel** (when you set `access_key:secret_key`) **or** from **Config (env)** when you leave the Bedrock API key blank.

- **No active config / fallback Bedrock**  
  - Uses the module‑level Bedrock client, which is built from **Config** (env) or from the **default credential chain** (see below).

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

- **Access key and secret key** = either from **env (Config)** or from **IAM** (when you don’t set them in env).
- **Admin panel** = only for the **AI assistant** (OpenAI key or Bedrock `access_key:secret_key` / fallback to env).

---

## 4. How Docker fits in (credentials and pipeline)

- **No secrets in the image**  
  The Dockerfile does **not** bake in any API or AWS keys. All credentials are provided at **runtime**.

- **Startup order in the container**
  1. Container starts → runs `app:app` (e.g. gunicorn).
  2. **Before** loading Flask/Config, `app.py` runs `load_into_env()`. If `AWS_SECRETS_INSIGHTSHOP` is set, the app calls Secrets Manager (using the **default credential chain**: env or IAM) and pushes secret key/values into `os.environ`.
  3. Then `Config` is loaded from `os.environ` (and `.env` if present). So `JWT_SECRET`, `SECRET_KEY`, and optionally `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` can come from the secret.
  4. When a user hits the AI assistant, the **active** AI Assistant config (from the DB) is used. For Bedrock, credentials are chosen as in section 2 (admin `access_key:secret_key` or Config env).

- **Ways to supply credentials in Docker**

  | Scenario | How access/secret key are supplied | Admin panel role |
  |----------|-----------------------------------|-------------------|
  | **Docker on your machine** | `--env-file` or `-e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=...` (or `aws configure` on host and pass through if you mount AWS config). | You can leave Bedrock “API key” blank and use env; or set `access_key:secret_key` in admin. |
  | **Docker on AWS (App Runner / ECS)** | Prefer **IAM role** for the task/service. Don’t set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in env; boto3 uses the role. Optionally inject other secrets (e.g. `JWT_SECRET`) from Secrets Manager in the service config. | Same: Bedrock can use “API key” blank → then pipeline uses IAM via default chain; or set keys in admin. |
  | **Secrets Manager at startup** | Set env `AWS_SECRETS_INSIGHTSHOP=insightshop/production`. Container needs permission to read that secret (env keys or IAM). After `load_into_env()`, `Config` can get `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` from the secret. | Still applies: admin panel overrides only the **AI assistant** Bedrock credentials when you set them. |

So in Docker:

- **Access key and secret key** for the rest of the pipeline (Polly, SES, S3, fallback Bedrock, optional Secrets Manager fetch) come from **environment** (set by you or by Secrets Manager at startup) or from **IAM** when nothing is set.
- The **admin-panel API key** only affects the **AI assistant** (OpenAI key or Bedrock `access_key:secret_key` or “use env/IAM”).

---

## 5. Short summary

- **Access key and secret key** = AWS IAM credentials. They come from:
  - **Environment** (Config): `.env`, Docker `-e` / `--env-file`, or App Runner/Secrets Manager injecting into env.
  - **IAM role** (when running on AWS and you don’t set keys in env).
  - Optionally **admin panel** for **Bedrock only**: put `access_key:secret_key` in the AI Assistant “API key” field so the **assistant pipeline** uses those instead of Config/IAM.
- **Rest of pipeline with Docker:**  
  Env (or IAM) → `load_into_env()` (optional) → Config → app uses Config / default chain for AWS; AI chat uses active admin config and, for Bedrock, admin key or Config/IAM as above.
