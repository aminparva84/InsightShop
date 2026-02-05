"""
Verify AWS credentials and connectivity.
Run from project root: python scripts/verify_aws_connection.py
Loads .env via config (dotenv).
"""
import os
import sys

# Load .env and config from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from config import Config


def main():
    print("Checking AWS configuration...")
    print("  AWS_REGION:", Config.AWS_REGION or "(not set)")
    print("  AWS_ACCESS_KEY_ID:", "***" + (Config.AWS_ACCESS_KEY_ID[-4:] if Config.AWS_ACCESS_KEY_ID else "(not set)"))
    print("  AWS_SECRET_ACCESS_KEY:", "***set***" if Config.AWS_SECRET_ACCESS_KEY else "(not set)")

    if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
        print("\nERROR: Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env")
        sys.exit(1)

    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        print("\nERROR: boto3 not installed. Run: pip install boto3")
        sys.exit(1)

    try:
        sts = boto3.client(
            "sts",
            region_name=Config.AWS_REGION or "us-east-1",
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        )
        identity = sts.get_caller_identity()
        print("\nAWS connection OK")
        print("  Account:", identity.get("Account"))
        print("  ARN:", identity.get("Arn"))
        print("  UserId:", identity.get("UserId"))
        return 0
    except NoCredentialsError:
        print("\nERROR: Invalid or missing credentials")
        sys.exit(1)
    except ClientError as e:
        print("\nERROR:", e.response.get("Error", {}).get("Message", str(e)))
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
