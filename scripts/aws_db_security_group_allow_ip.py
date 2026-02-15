#!/usr/bin/env python3
"""
Create an AWS security group that allows PostgreSQL (port 5432) only from 18.193.0.149.
Use this SG for your RDS instance so only that IP (e.g. DBeaver) can connect to the DB.

Requires: AWS CLI configured (or env AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION).
Usage:
  python scripts/aws_db_security_group_allow_ip.py --vpc-id vpc-xxxxxxxxx [--region us-east-1] [--attach-rds your-db-id]
"""
import argparse
import sys

# Allow running from project root
try:
    from config import Config
except ImportError:
    Config = None

ALLOWED_IP = "18.193.0.149/32"
PORT = 5432
SG_NAME = "insightshop-db-admin-only"
SG_DESCRIPTION = "PostgreSQL (5432) access only from 18.193.0.149"


def get_region(args):
    if args.region:
        return args.region
    if Config and getattr(Config, "AWS_REGION", None):
        return Config.AWS_REGION
    import os
    return os.environ.get("AWS_REGION", "us-east-1")


def get_ec2_client(region):
    import boto3
    kwargs = {"region_name": region}
    if Config and Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY
    return boto3.client("ec2", **kwargs)


def get_rds_client(region):
    import boto3
    kwargs = {"region_name": region}
    if Config and Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY
    return boto3.client("rds", **kwargs)


def create_security_group(ec2, vpc_id):
    from botocore.exceptions import ClientError
    try:
        r = ec2.create_security_group(
            GroupName=SG_NAME,
            Description=SG_DESCRIPTION,
            VpcId=vpc_id,
        )
        sg_id = r["GroupId"]
        print(f"Created security group: {sg_id}")
        return sg_id
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "InvalidGroup.Duplicate" or "already exists" in str(e).lower():
            sgs = ec2.describe_security_groups(
                Filters=[
                    {"Name": "group-name", "Values": [SG_NAME]},
                    {"Name": "vpc-id", "Values": [vpc_id]},
                ]
            )
            if sgs.get("SecurityGroups"):
                sg_id = sgs["SecurityGroups"][0]["GroupId"]
                print(f"Security group already exists: {sg_id}")
                return sg_id
        raise


def add_ingress_rule(ec2, sg_id):
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    "FromPort": PORT,
                    "ToPort": PORT,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": ALLOWED_IP, "Description": "DBeaver/admin IP only"}],
                }
            ],
        )
        print(f"Added rule: TCP {PORT} from {ALLOWED_IP}")
    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e).lower():
            print(f"Rule already present: TCP {PORT} from {ALLOWED_IP}")
        else:
            raise


def attach_to_rds(rds_client, db_id, sg_id):
    """Add this SG to the RDS instance. Keeps existing SGs; RDS requires at least one SG."""
    try:
        desc = rds_client.describe_db_instances(DBInstanceIdentifier=db_id)
        if not desc.get("DBInstances"):
            print(f"RDS instance not found: {db_id}", file=sys.stderr)
            return False
        current_sgs = [s["VpcSecurityGroupId"] for s in desc["DBInstances"][0].get("VpcSecurityGroups", [])]
        if sg_id in current_sgs:
            print(f"RDS {db_id} already uses security group {sg_id}")
            return True
        new_sgs = list(current_sgs) + [sg_id]
        rds_client.modify_db_instance(
            DBInstanceIdentifier=db_id,
            VpcSecurityGroupIds=new_sgs,
            ApplyImmediately=True,
        )
        print(f"Attached {sg_id} to RDS instance {db_id}. ApplyImmediately=True.")
        return True
    except Exception as e:
        print(f"Failed to attach SG to RDS: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create SG allowing PostgreSQL only from 18.193.0.149 and optionally attach to RDS."
    )
    parser.add_argument("--vpc-id", required=True, help="VPC ID where RDS (or target resource) lives")
    parser.add_argument("--region", default=None, help="AWS region (default: config or us-east-1)")
    parser.add_argument("--attach-rds", metavar="DB_ID", default=None, help="RDS instance id to attach the new SG to")
    args = parser.parse_args()

    region = get_region(args)
    ec2 = get_ec2_client(region)

    sg_id = create_security_group(ec2, args.vpc_id)
    add_ingress_rule(ec2, sg_id)

    if args.attach_rds:
        rds = get_rds_client(region)
        attach_to_rds(rds, args.attach_rds, sg_id)
    else:
        print("\nNext: In AWS Console RDS → your DB → Modify → add Security group:", sg_id)
        print("Or run: --attach-rds <your-db-instance-id>")

    print("\nDone. Only 18.193.0.149 can connect to port 5432 where this SG is used.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
