# AWS Connection

InsightShop uses AWS for several features. This doc describes how the connection is configured and how to verify it.

## How credentials are loaded

1. **Environment**: The app reads `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` from the environment.
2. **`.env` file**: When you run locally, `python-dotenv` loads these from a `.env` file in the project root (see `config.py`). The `.env` file is **gitignored** and must never be committed.
3. **AWS services used**:
   - **Polly** — Text-to-speech for the AI agent
   - **S3** — Optional DB/image backups (`scripts/backup_to_s3.py`, `scripts/restore_from_s3.py`)
   - **SES** — Email (`utils/email.py`)
   - **Secrets Manager** — Optional: set `AWS_SECRETS_INSIGHTSHOP` to a secret name to load env from AWS (`utils/secrets_loader.py`)

## Verify connection

From the project root:

```bash
python scripts/verify_aws_connection.py
```

This calls AWS STS `GetCallerIdentity` and prints your account ID and ARN. If it succeeds, Polly/S3/SES will use the same credentials (subject to IAM permissions).

## Setting credentials locally

- **Option A**: Edit `.env` and set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_REGION`.
- **Option B**: Run `python scripts/set_aws_env.py <ACCESS_KEY_ID> <SECRET_ACCESS_KEY>` to add or update these in `.env`.

## Production (App Runner / ECS)

On AWS, do **not** put long-lived access keys in the environment if you can avoid it:

- **App Runner / ECS**: Attach an IAM role to the task/service. The SDK will use the role automatically; you do not need to set `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`.
- **Other secrets**: Use AWS Secrets Manager and reference the secret with `AWS_SECRETS_INSIGHTSHOP`, or inject secrets as environment variables from your deployment config.

## If you shared your keys

If your AWS access key or secret was ever shared (e.g. in chat or email):

1. In AWS Console go to **IAM → Users → your user → Security credentials**.
2. Create a new access key.
3. Update your `.env` (or deployment config) with the new key.
4. **Delete the old access key** so it can no longer be used.
