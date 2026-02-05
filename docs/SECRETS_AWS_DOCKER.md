# Safe API Key and Secret Setup (AWS + Docker)

This guide describes the **safe and recommended** way to provide your **assistant API key** and **secret key** (e.g. JWT) when running InsightShop with **AWS** and **Docker**.

For how **AWS access key / secret key** and the **admin-panel API key** interact, and how the pipeline works with Docker, see **[PIPELINE_AWS_AND_DOCKER.md](PIPELINE_AWS_AND_DOCKER.md)**.

## Principles

- **Never** commit API keys or secrets to git.
- **Never** bake secrets into Docker images.
- Store secrets in **AWS Secrets Manager** and inject them at runtime via environment variables (or optional startup fetch).
- Prefer **IAM roles** for AWS services (App Runner/ECS) so the app can read secrets without storing AWS access keys.

---

## 1. Create the secret in AWS Secrets Manager

Create one JSON secret that holds your app and assistant credentials.

### Using AWS CLI

```bash
aws secretsmanager create-secret \
  --name insightshop/production \
  --description "InsightShop app and assistant secrets" \
  --secret-string '{
    "JWT_SECRET": "YOUR_LONG_RANDOM_JWT_SECRET_MIN_32_CHARS",
    "SECRET_KEY": "YOUR_FLASK_SECRET_KEY"
  }' \
  --region us-east-1
```

To add or update keys later:

```bash
aws secretsmanager put-secret-value \
  --secret-id insightshop/production \
  --secret-string '{
    "JWT_SECRET": "...",
    "SECRET_KEY": "..."
  }' \
  --region us-east-1
```

### Optional keys you can include

| Key | Purpose |
|-----|--------|
| `JWT_SECRET` | Auth tokens (min 32 chars in production) |
| `SECRET_KEY` | Flask session signing |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Only if you cannot use an IAM role (e.g. local Docker) |

**AI Assistant API key:** The app uses only the API key that the admin configures in **Admin → AI Assistant**. Store that key in the admin panel (or paste a value you keep in Secrets Manager); it is not read from environment variables.

**Best practice:** On App Runner/ECS, do **not** put AWS credentials in the secret; use an IAM role for the service instead.

---

## 2. App Runner (recommended for production)

App Runner can inject secrets from Secrets Manager as environment variables. No code change required.

### In AWS Console

1. **App Runner** → your service → **Configuration** → **Edit**.
2. Under **Security** (or **Environment variables**), add **Secrets**.
3. For each variable:
   - **Source:** AWS Secrets Manager
   - **Secret:** select `insightshop/production` (or your secret name).
   - **Key:** the JSON key (e.g. `JWT_SECRET`, `ASSISTANT_API_KEY`).
   - **Value (env name):** the environment variable name the app expects, e.g. `JWT_SECRET`, `ASSISTANT_API_KEY`.

Map at least:

- `JWT_SECRET` → env `JWT_SECRET`
- `SECRET_KEY` → env `SECRET_KEY`

The app reads these via `config.py` from `os.environ`. The AI assistant API key is configured only in **Admin → AI Assistant** (not from env).

### Alternative: fetch at startup

If you prefer one secret and don’t want to map each key in the console:

1. In App Runner, add a **single** environment variable:
   - Name: `AWS_SECRETS_INSIGHTSHOP`
   - Value: `insightshop/production` (your secret name or ARN).
2. Ensure the App Runner instance role has `secretsmanager:GetSecretValue` for that secret.
3. At startup the app will fetch the secret and set **all** JSON keys as environment variables (see `utils/secrets_loader.py`). Existing env vars are **not** overwritten.

---

## 3. Docker (local or any host)

Secrets must **not** be in the image. Pass them at runtime.

**Step-by-step:** See **[DOCKER_RUN.md](DOCKER_RUN.md)** for using an env file with `docker-compose` or `docker run --env-file .env`.

### Option A: Env file (local only, never commit)

Create a file `.env.production` (or `.env`) and add it to `.gitignore`:

```env
JWT_SECRET=your-long-random-jwt-secret-min-32-chars
SECRET_KEY=your-flask-secret-key
```

Run:

```bash
docker build -t insightshop:latest .
docker run --env-file .env.production -p 5000:5000 insightshop:latest
```

### Option B: Fetch from AWS at container startup

If the host (or container) has AWS credentials or an IAM role:

1. Set the secret name in an env var:
   ```bash
   docker run -e AWS_SECRETS_INSIGHTSHOP=insightshop/production -e AWS_REGION=us-east-1 -p 5000:5000 insightshop:latest
   ```
2. Provide AWS credentials via env or IAM role so the app can call `secretsmanager:GetSecretValue`. The app will load the secret and set env vars before loading config.

Example with host AWS profile:

```bash
docker run --env-file .env.aws \
  -e AWS_SECRETS_INSIGHTSHOP=insightshop/production \
  -e AWS_REGION=us-east-1 \
  -p 5000:5000 insightshop:latest
```

Where `.env.aws` only has non-secret vars (e.g. `AWS_REGION`) or you pass credentials via `-e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=...` (only for dev; prefer IAM in production).

### Option C: Docker Compose

```yaml
services:
  app:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env.production   # gitignored; contains JWT_SECRET, SECRET_KEY
    environment:
      - FLASK_ENV=production
```

Or use the startup fetch:

```yaml
    environment:
      - AWS_SECRETS_INSIGHTSHOP=insightshop/production
      - AWS_REGION=us-east-1
    # Ensure AWS credentials are available (e.g. env_file with AWS_* or IAM)
```

---

## 4. How the app uses the assistant API key

- **JWT_SECRET / SECRET_KEY:** Read from environment in `config.py`; can be provided by Secrets Manager or env file.
- **AI Assistant API key:** The app uses **only** the API key that the admin enables in **Admin → AI Assistant**. That value is stored in the database (`ai_assistant_configs.api_key`). There is no fallback to environment variables—the admin panel is the single source of truth for the assistant API key.

---

## 5. IAM permissions (when using startup fetch or Parameter Store)

If the app fetches the secret at startup (e.g. `AWS_SECRETS_INSIGHTSHOP` set), the execution role must allow:

```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:insightshop/production-*"
}
```

Replace `ACCOUNT_ID` and region/secret name as needed.

---

## 6. Summary

| Where you run | How to provide assistant + secret key |
|---------------|--------------------------------------|
| **App Runner** | Add secrets from Secrets Manager in service config (or set `AWS_SECRETS_INSIGHTSHOP` and grant IAM `GetSecretValue`). |
| **Docker on AWS (ECS, etc.)** | Use task role with `GetSecretValue`; set `AWS_SECRETS_INSIGHTSHOP` or inject env from Secrets Manager in task definition. |
| **Docker locally** | `--env-file` with a gitignored file, or `-e AWS_SECRETS_INSIGHTSHOP=...` and AWS credentials. |

The **AI assistant API key** is never read from env or config: it is only the value the admin sets in **Admin → AI Assistant**, so it is never hardcoded.
