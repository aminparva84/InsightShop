# Run InsightShop with Docker (env file for AWS keys)

Use this flow to run the app in Docker and pass your **AWS access key and secret key** (and other secrets) via an env file.

---

## 1. Create your env file

Copy the example and edit it with your values (do not commit `.env`):

```bash
copy env.docker.example .env
```

Edit `.env` and set at least:

- **JWT_SECRET** – long random string (min 32 characters)
- **SECRET_KEY** – same or another long random string
- **AWS_ACCESS_KEY_ID** – your AWS access key
- **AWS_SECRET_ACCESS_KEY** – your AWS secret key
- **AWS_REGION** – e.g. `us-east-1`

---

## 2. Run with Docker

### Option A: docker-compose (recommended)

Builds the image, loads `.env`, and persists the database and vector DB in Docker volumes:

```bash
docker-compose up --build
```

Open **http://localhost:5000**. To run in the background: `docker-compose up -d --build`.

### Option B: Plain docker run

Build once:

```bash
docker build -t insightshop:latest .
```

Run with your env file:

```bash
docker run --rm -p 5000:5000 --env-file .env insightshop:latest
```

Data is not persisted between runs unless you add volume mounts (e.g. `-v insightshop_instance:/app/instance`).

### Option C: Windows script

From the project root:

```bash
docker-run.bat
```

This checks for `.env`, builds the image, and runs with `--env-file .env`. It does not use volumes; use docker-compose if you need persistence.

---

## 3. After the app is running

- The app uses **Config** (env) for AWS (Polly, S3, SES, Secrets Manager). **Admin → AI Assistant** uses simple API keys for OpenAI, Gemini, and Anthropic — see [AI_PROVIDERS_SETUP.md](AI_PROVIDERS_SETUP.md).

---

## Files added for this approach

| File | Purpose |
|------|--------|
| **env.docker.example** | Template for `.env` (AWS keys, JWT_SECRET, SECRET_KEY). Copy to `.env` and fill in. |
| **docker-compose.yml** | Build + run with `env_file: .env` and persistent volumes for DB and vector DB. |
| **docker-run.bat** | Windows: build and run with `--env-file .env` (no volumes). |
