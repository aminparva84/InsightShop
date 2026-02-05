"""
One-time script to set AWS credentials in .env.
Run: python scripts/set_aws_env.py
Uses values from environment or from the optional KEY/SECRET args (for initial setup).
Never commit .env; it is in .gitignore.
"""
import os
import sys

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def main():
    key_id = os.getenv("AWS_ACCESS_KEY_ID") or (sys.argv[1] if len(sys.argv) > 1 else "")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY") or (sys.argv[2] if len(sys.argv) > 2 else "")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not key_id or not secret:
        print("Usage: set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in env, or run:")
        print("  python scripts/set_aws_env.py <ACCESS_KEY_ID> <SECRET_ACCESS_KEY>")
        sys.exit(1)

    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("AWS_ACCESS_KEY_ID=") or stripped.startswith("AWS_SECRET_ACCESS_KEY=") or stripped.startswith("AWS_REGION="):
                    continue
                lines.append(line.rstrip("\n"))
        if lines and lines[-1].strip():
            lines.append("")
    else:
        lines = ["# InsightShop environment - do not commit", ""]

    lines.append("AWS_ACCESS_KEY_ID=" + key_id)
    lines.append("AWS_SECRET_ACCESS_KEY=" + secret)
    lines.append("AWS_REGION=" + region)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("Updated .env with AWS credentials (AWS_REGION=%s)." % region)
    print("Verify: python scripts/verify_aws_connection.py")


if __name__ == "__main__":
    main()
