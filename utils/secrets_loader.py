"""
Load application secrets from AWS Secrets Manager into environment variables.

Safe usage with AWS and Docker:
- Store secrets in AWS Secrets Manager (never in code or committed .env).
- When running on AWS (App Runner, ECS, Lambda), use IAM role; no access keys in the secret.
- Set env var AWS_SECRETS_INSIGHTSHOP to the secret name/ARN to enable fetch at startup.
- Alternatively, inject secrets as env vars from Secrets Manager in the service config (App Runner/ECS).
"""
import json
import os


def load_into_env():
    """
    If AWS_SECRETS_INSIGHTSHOP is set, fetch that secret from AWS Secrets Manager
    and set os.environ for each key in the secret JSON. Only sets variables that
    are not already set, so explicit env vars take precedence.
    """
    secret_name = os.getenv("AWS_SECRETS_INSIGHTSHOP")
    if not secret_name:
        return

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return

    region = os.getenv("AWS_REGION", "us-east-1")
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ResourceNotFoundException", "AccessDeniedException"):
            return
        raise
    except Exception:
        return

    raw = response.get("SecretString")
    if not raw:
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    if not isinstance(data, dict):
        return

    for key, value in data.items():
        if key in os.environ:
            continue
        if value is not None and not isinstance(value, (dict, list)):
            os.environ[key] = str(value)
