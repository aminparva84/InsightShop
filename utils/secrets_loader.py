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

# Default secret name to try when env is not set (e.g. production with IAM role)
DEFAULT_SECRET_NAMES = ("insightshop/production", "insightshop-secrets", "insightshop/prod")

# Keys we look for in the secret for Gemini (first match wins)
GEMINI_KEY_NAMES = ("GEMINI_API_KEY", "gemini_api_key", "GeminiApiKey", "GEMINI_KEY")


def _fetch_secret_json(secret_name):
    """Fetch secret from AWS Secrets Manager; return parsed JSON dict or None."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return None
    region = os.getenv("AWS_REGION", "us-east-1")
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
    except Exception:
        return None
    raw = response.get("SecretString") if response else None
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def get_gemini_api_key_from_aws():
    """
    Fetch Gemini API key from AWS Secrets Manager. Tries AWS_SECRETS_INSIGHTSHOP first,
    then default secret names. Returns the key string or None. Also sets os.environ['GEMINI_API_KEY']
    so future lookups see it.
    """
    secret_name = os.getenv("AWS_SECRETS_INSIGHTSHOP")
    names_to_try = [secret_name] if secret_name else []
    names_to_try.extend(DEFAULT_SECRET_NAMES)
    for name in names_to_try:
        if not name:
            continue
        data = _fetch_secret_json(name)
        if not data:
            continue
        for key in GEMINI_KEY_NAMES:
            val = data.get(key)
            if val and not isinstance(val, (dict, list)):
                key_str = str(val).strip()
                if key_str:
                    os.environ["GEMINI_API_KEY"] = key_str
                    return key_str
    return None


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

    # Map common secret key names to env vars the app expects
    KEY_ALIASES = {
        "GEMINI_API_KEY": ("GEMINI_API_KEY", "gemini_api_key", "GeminiApiKey", "GEMINI_KEY"),
        "OPENAI_API_KEY": ("OPENAI_API_KEY", "openai_api_key", "OpenAIApiKey", "OPENAI_KEY"),
        "ANTHROPIC_API_KEY": ("ANTHROPIC_API_KEY", "anthropic_api_key", "AnthropicApiKey", "ANTHROPIC_KEY"),
    }

    for key, value in data.items():
        if value is None or isinstance(value, (dict, list)):
            continue
        value_str = str(value)
        # Set the key as-is if not already in env
        if key not in os.environ:
            os.environ[key] = value_str
        # Also set standard env name if this key is an alias for a known var
        for standard_name, aliases in KEY_ALIASES.items():
            if key in aliases and standard_name not in os.environ:
                os.environ[standard_name] = value_str
                break
