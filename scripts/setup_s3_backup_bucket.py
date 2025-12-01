"""
Setup S3 bucket for InsightShop backups with proper configuration.
"""
import boto3
import json
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_backup_bucket(bucket_name, region='us-east-1'):
    """Create S3 bucket for backups with proper configuration."""
    try:
        s3_client = boto3.client('s3', region_name=region)
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"✅ Bucket '{bucket_name}' already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != '404':
                raise
        
        # Create bucket
        logger.info(f"Creating bucket '{bucket_name}' in region '{region}'...")
        
        if region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        logger.info(f"✅ Bucket '{bucket_name}' created successfully")
        
        # Configure bucket settings
        configure_bucket(s3_client, bucket_name)
        
        return True
        
    except ClientError as e:
        logger.error(f"❌ Failed to create bucket: {e}")
        return False

def configure_bucket(s3_client, bucket_name):
    """Configure bucket with versioning, encryption, and lifecycle policies."""
    
    # Enable versioning
    try:
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        logger.info("✅ Versioning enabled")
    except Exception as e:
        logger.warning(f"Failed to enable versioning: {e}")
    
    # Enable encryption
    try:
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }]
            }
        )
        logger.info("✅ Encryption enabled")
    except Exception as e:
        logger.warning(f"Failed to enable encryption: {e}")
    
    # Block public access
    try:
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        logger.info("✅ Public access blocked")
    except Exception as e:
        logger.warning(f"Failed to block public access: {e}")
    
    # Set lifecycle policy (move to Glacier after 90 days, delete after 1 year)
    try:
        lifecycle_policy = {
            'Rules': [
                {
                    'Id': 'MoveToGlacier',
                    'Status': 'Enabled',
                    'Prefix': 'backups/',
                    'Transitions': [
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        }
                    ],
                    'Expiration': {
                        'Days': 365
                    }
                }
            ]
        }
        
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_policy
        )
        logger.info("✅ Lifecycle policy configured (Glacier after 90 days, delete after 1 year)")
    except Exception as e:
        logger.warning(f"Failed to set lifecycle policy: {e}")
    
    # Add tags
    try:
        s3_client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {'Key': 'Purpose', 'Value': 'InsightShop Backups'},
                    {'Key': 'ManagedBy', 'Value': 'InsightShop Backup Script'}
                ]
            }
        )
        logger.info("✅ Tags added")
    except Exception as e:
        logger.warning(f"Failed to add tags: {e}")

def main():
    """Main setup function."""
    import sys
    
    bucket_name = sys.argv[1] if len(sys.argv) > 1 else 'insightshop-backups'
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-east-1'
    
    logger.info("=" * 50)
    logger.info("Setting up S3 Backup Bucket")
    logger.info(f"Bucket: {bucket_name}")
    logger.info(f"Region: {region}")
    logger.info("=" * 50)
    
    success = create_backup_bucket(bucket_name, region)
    
    if success:
        logger.info("=" * 50)
        logger.info("✅ S3 bucket setup complete!")
        logger.info(f"Bucket: {bucket_name}")
        logger.info("\nNext steps:")
        logger.info("1. Set environment variable: S3_BACKUP_BUCKET=" + bucket_name)
        logger.info("2. Run backup script: python scripts/backup_to_s3.py")
        logger.info("=" * 50)
    else:
        logger.error("❌ Setup failed. Check logs above.")
    
    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

