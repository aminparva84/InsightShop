"""
Secure storage for API keys and secrets in the database.
- Optional encryption at rest when ENCRYPTION_KEY is set (32-byte URL-safe base64, or 32+ char string).
- Never log or expose raw values.
"""
import os
import base64
import hashlib

# Prefix for values we encrypt (so we can detect and decrypt on read)
_ENC_PREFIX = "enc:"


def _get_fernet_key():
    """Derive a valid Fernet key from ENCRYPTION_KEY env. Returns None if not set."""
    raw = os.getenv("ENCRYPTION_KEY") or os.getenv("AI_KEYS_ENCRYPTION_KEY", "").strip()
    if not raw or len(raw) < 16:
        return None
    # Fernet needs 32 bytes base64-encoded; we hash to get 32 bytes then base64
    key_bytes = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_plaintext(plain: str) -> str:
    """Encrypt a string for storage. Returns prefixed ciphertext or original if encryption disabled."""
    if not plain or not plain.strip():
        return plain or ""
    key = _get_fernet_key()
    if not key:
        return plain
    try:
        from cryptography.fernet import Fernet
        f = Fernet(key)
        enc = f.encrypt(plain.encode("utf-8"))
        return _ENC_PREFIX + enc.decode("ascii")
    except Exception:
        return plain


def decrypt_ciphertext(value: str) -> str:
    """Decrypt a stored value. Returns plaintext; if not encrypted or decrypt fails, returns as-is."""
    if not value or not value.strip():
        return value or ""
    if not value.startswith(_ENC_PREFIX):
        return value
    key = _get_fernet_key()
    if not key:
        return value
    try:
        from cryptography.fernet import Fernet
        f = Fernet(key)
        dec = f.decrypt(value[len(_ENC_PREFIX):].encode("ascii"))
        return dec.decode("utf-8")
    except Exception:
        return value


def redact_for_log(data: dict, keys=None) -> dict:
    """Return a copy of data with sensitive keys replaced by '***'. Never log the original."""
    if keys is None:
        keys = ("api_key", "access_key_id", "secret_access_key", "password", "secret")
    out = dict(data)
    for k in keys:
        if k in out and out[k] is not None and out[k] != "":
            out[k] = "***"
    return out
