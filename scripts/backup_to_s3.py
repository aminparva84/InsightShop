"""
Automated backup script for InsightShop databases to S3.
Backs up PostgreSQL (when DATABASE_URL is set) or SQLite, and ChromaDB vector database.
"""
import boto3
from datetime import datetime
from config import Config
import os
import subprocess
import tarfile
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_s3_client():
    """Initialize S3 client with credentials from config."""
    try:
        s3_client = boto3.client(
            's3',
            region_name=Config.AWS_REGION,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID if Config.AWS_ACCESS_KEY_ID else None,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY if Config.AWS_SECRET_ACCESS_KEY else None
        )
        return s3_client
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        return None

def backup_postgres_database(s3_client, bucket_name, instance_id=None):
    """Backup PostgreSQL database to S3 using pg_dump."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_dir = os.environ.get('TEMP', os.environ.get('TMP', '/tmp'))
        if not os.path.exists(temp_dir):
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        dump_path = os.path.join(temp_dir, f'insightshop_pg_{timestamp}.sql')

        logger.info("Running pg_dump...")
        result = subprocess.run(
            ['pg_dump', '--no-password', '--clean', '--if-exists', '--file', dump_path, Config.DATABASE_URL],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"pg_dump failed: {result.stderr}")
            return False
        if not os.path.exists(dump_path):
            logger.error("pg_dump did not create output file")
            return False

        if instance_id:
            backup_key = f"backups/{instance_id}/database/insightshop_{timestamp}.sql"
        else:
            backup_key = f"backups/database/insightshop_{timestamp}.sql"

        logger.info(f"Backing up database to s3://{bucket_name}/{backup_key}")
        s3_client.upload_file(
            dump_path,
            bucket_name,
            backup_key,
            ExtraArgs={'ServerSideEncryption': 'AES256', 'StorageClass': 'STANDARD_IA'}
        )
        logger.info(f"✅ Database backup successful: {backup_key}")

        latest_key = backup_key.replace(f"_{timestamp}", "_latest")
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': backup_key},
            Key=latest_key,
            ServerSideEncryption='AES256',
            StorageClass='STANDARD_IA'
        )
        logger.info(f"✅ Latest backup created: {latest_key}")

        try:
            os.remove(dump_path)
        except Exception:
            pass
        return True
    except FileNotFoundError:
        logger.error("pg_dump not found. Install PostgreSQL client tools.")
        return False
    except Exception as e:
        logger.error(f"❌ PostgreSQL backup failed: {e}")
        return False


def backup_sqlite_database(s3_client, bucket_name, instance_id=None):
    """Backup SQLite database to S3."""
    try:
        # Get database path
        db_path = Config.DB_PATH
        if not os.path.isabs(db_path):
            # Relative path - check instance folder
            instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
            db_path = os.path.join(instance_path, db_path)
        
        if not os.path.exists(db_path):
            logger.warning(f"Database file not found at {db_path}")
            return False
        
        # Create timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create backup key
        if instance_id:
            backup_key = f"backups/{instance_id}/database/insightshop_{timestamp}.db"
        else:
            backup_key = f"backups/database/insightshop_{timestamp}.db"
        
        # Upload to S3
        logger.info(f"Backing up database to s3://{bucket_name}/{backup_key}")
        s3_client.upload_file(
            db_path,
            bucket_name,
            backup_key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',
                'StorageClass': 'STANDARD_IA'  # Infrequent Access for cost savings
            }
        )
        
        logger.info(f"✅ Database backup successful: {backup_key}")
        
        # Also create a "latest" backup for easy restore
        latest_key = backup_key.replace(f"_{timestamp}", "_latest")
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': backup_key},
            Key=latest_key,
            ServerSideEncryption='AES256',
            StorageClass='STANDARD_IA'
        )
        logger.info(f"✅ Latest backup created: {latest_key}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database backup failed: {e}")
        return False

def backup_chromadb(s3_client, bucket_name, instance_id=None):
    """Backup ChromaDB vector database to S3."""
    try:
        vector_db_path = Config.VECTOR_DB_PATH
        if not os.path.isabs(vector_db_path):
            vector_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', vector_db_path)
        
        if not os.path.exists(vector_db_path):
            logger.warning(f"Vector DB directory not found at {vector_db_path}")
            return False
        
        # Create timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create temporary tar file
        temp_dir = '/tmp' if os.path.exists('/tmp') else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        tar_filename = os.path.join(temp_dir, f'vector_db_{timestamp}.tar.gz')
        
        # Create tar archive
        logger.info(f"Creating tar archive of vector database...")
        with tarfile.open(tar_filename, 'w:gz') as tar:
            tar.add(vector_db_path, arcname='vector_db', recursive=True)
        
        # Create backup key
        if instance_id:
            backup_key = f"backups/{instance_id}/vector_db/vector_db_{timestamp}.tar.gz"
        else:
            backup_key = f"backups/vector_db/vector_db_{timestamp}.tar.gz"
        
        # Upload to S3
        logger.info(f"Backing up vector database to s3://{bucket_name}/{backup_key}")
        s3_client.upload_file(
            tar_filename,
            bucket_name,
            backup_key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',
                'StorageClass': 'STANDARD_IA'  # Infrequent Access for cost savings
            }
        )
        
        logger.info(f"✅ Vector DB backup successful: {backup_key}")
        
        # Also create a "latest" backup for easy restore
        latest_key = backup_key.replace(f"_{timestamp}", "_latest")
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': backup_key},
            Key=latest_key,
            ServerSideEncryption='AES256',
            StorageClass='STANDARD_IA'
        )
        logger.info(f"✅ Latest vector DB backup created: {latest_key}")
        
        # Clean up temp file
        if os.path.exists(tar_filename):
            os.remove(tar_filename)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector DB backup failed: {e}")
        return False

def cleanup_old_backups(s3_client, bucket_name, instance_id=None, keep_days=30):
    """Delete backups older than keep_days."""
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        prefix = f"backups/{instance_id}/" if instance_id else "backups/"
        
        # List all backups
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        deleted_count = 0
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                # Skip "latest" backups
                if '_latest' in obj['Key']:
                    continue
                
                # Check if object is older than cutoff
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    logger.info(f"Deleting old backup: {obj['Key']}")
                    s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                    deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"✅ Cleaned up {deleted_count} old backups")
        else:
            logger.info("No old backups to clean up")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return 0

def main():
    """Main backup function."""
    # Get S3 bucket name from environment or config
    bucket_name = os.getenv('S3_BACKUP_BUCKET', 'insightshop-backups')
    instance_id = os.getenv('INSTANCE_ID', None)  # For multi-tenant SaaS
    
    logger.info("=" * 50)
    logger.info("Starting InsightShop Backup Process")
    logger.info(f"Bucket: {bucket_name}")
    logger.info(f"Instance ID: {instance_id or 'default'}")
    logger.info("=" * 50)
    
    # Initialize S3 client
    s3_client = get_s3_client()
    if not s3_client:
        logger.error("Failed to initialize S3 client. Exiting.")
        return False
    
    # Verify bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"✅ Bucket '{bucket_name}' exists")
    except s3_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            logger.error(f"❌ Bucket '{bucket_name}' does not exist. Please create it first.")
            logger.info(f"Create bucket with: aws s3 mb s3://{bucket_name}")
            return False
        else:
            logger.error(f"❌ Error accessing bucket: {e}")
            return False
    
    # Perform backups: PostgreSQL if DATABASE_URL set, else SQLite
    if Config.DATABASE_URL:
        db_success = backup_postgres_database(s3_client, bucket_name, instance_id)
    else:
        db_success = backup_sqlite_database(s3_client, bucket_name, instance_id)
    vector_success = backup_chromadb(s3_client, bucket_name, instance_id)
    
    # Cleanup old backups (keep last 30 days)
    cleanup_old_backups(s3_client, bucket_name, instance_id, keep_days=30)
    
    # Summary
    logger.info("=" * 50)
    if db_success and vector_success:
        logger.info("✅ All backups completed successfully!")
        return True
    else:
        logger.warning("⚠️ Some backups failed. Check logs above.")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

