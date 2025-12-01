"""
Restore InsightShop databases from S3 backups.
"""
import boto3
from datetime import datetime
from config import Config
import os
import tarfile
import logging
import shutil

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

def list_backups(s3_client, bucket_name, instance_id=None, backup_type='database'):
    """List available backups."""
    try:
        prefix = f"backups/{instance_id}/{backup_type}/" if instance_id else f"backups/{backup_type}/"
        
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return []
        
        backups = []
        for obj in response['Contents']:
            if '_latest' not in obj['Key']:  # Skip latest symlinks
                backups.append({
                    'key': obj['Key'],
                    'last_modified': obj['LastModified'],
                    'size': obj['Size']
                })
        
        # Sort by date (newest first)
        backups.sort(key=lambda x: x['last_modified'], reverse=True)
        return backups
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        return []

def restore_database(s3_client, bucket_name, backup_key, instance_id=None):
    """Restore SQLite database from S3."""
    try:
        # Get database path
        db_path = Config.DB_PATH
        if not os.path.isabs(db_path):
            instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
            os.makedirs(instance_path, exist_ok=True)
            db_path = os.path.join(instance_path, db_path)
        
        # Create backup of existing database if it exists
        if os.path.exists(db_path):
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Backing up existing database to {backup_path}")
            shutil.copy2(db_path, backup_path)
        
        # Download from S3
        logger.info(f"Downloading database from s3://{bucket_name}/{backup_key}")
        s3_client.download_file(bucket_name, backup_key, db_path)
        
        logger.info(f"✅ Database restored successfully to {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database restore failed: {e}")
        return False

def restore_chromadb(s3_client, bucket_name, backup_key, instance_id=None):
    """Restore ChromaDB vector database from S3."""
    try:
        vector_db_path = Config.VECTOR_DB_PATH
        if not os.path.isabs(vector_db_path):
            vector_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', vector_db_path)
        
        # Create backup of existing vector DB if it exists
        if os.path.exists(vector_db_path):
            backup_path = f"{vector_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Backing up existing vector DB to {backup_path}")
            if os.path.isdir(vector_db_path):
                shutil.copytree(vector_db_path, backup_path)
            else:
                shutil.copy2(vector_db_path, backup_path)
        
        # Download tar file
        temp_dir = '/tmp' if os.path.exists('/tmp') else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        tar_filename = os.path.join(temp_dir, os.path.basename(backup_key))
        
        logger.info(f"Downloading vector DB from s3://{bucket_name}/{backup_key}")
        s3_client.download_file(bucket_name, backup_key, tar_filename)
        
        # Extract tar file
        logger.info(f"Extracting vector DB to {vector_db_path}")
        os.makedirs(vector_db_path, exist_ok=True)
        
        with tarfile.open(tar_filename, 'r:gz') as tar:
            tar.extractall(os.path.dirname(vector_db_path))
        
        # Clean up temp file
        if os.path.exists(tar_filename):
            os.remove(tar_filename)
        
        logger.info(f"✅ Vector DB restored successfully to {vector_db_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector DB restore failed: {e}")
        return False

def main():
    """Main restore function."""
    import sys
    
    bucket_name = os.getenv('S3_BACKUP_BUCKET', 'insightshop-backups')
    instance_id = os.getenv('INSTANCE_ID', None)
    backup_type = sys.argv[1] if len(sys.argv) > 1 else 'latest'  # 'latest' or 'list' or specific timestamp
    
    logger.info("=" * 50)
    logger.info("InsightShop Restore Process")
    logger.info(f"Bucket: {bucket_name}")
    logger.info(f"Instance ID: {instance_id or 'default'}")
    logger.info("=" * 50)
    
    # Initialize S3 client
    s3_client = get_s3_client()
    if not s3_client:
        logger.error("Failed to initialize S3 client. Exiting.")
        return False
    
    if backup_type == 'list':
        # List available backups
        logger.info("\n📦 Available Database Backups:")
        db_backups = list_backups(s3_client, bucket_name, instance_id, 'database')
        for i, backup in enumerate(db_backups[:10], 1):
            logger.info(f"  {i}. {backup['key']} ({backup['last_modified']})")
        
        logger.info("\n📦 Available Vector DB Backups:")
        vector_backups = list_backups(s3_client, bucket_name, instance_id, 'vector_db')
        for i, backup in enumerate(vector_backups[:10], 1):
            logger.info(f"  {i}. {backup['key']} ({backup['last_modified']})")
        
        return True
    
    # Restore from backup
    if backup_type == 'latest':
        db_key = f"backups/{instance_id}/database/insightshop_latest.db" if instance_id else "backups/database/insightshop_latest.db"
        vector_key = f"backups/{instance_id}/vector_db/vector_db_latest.tar.gz" if instance_id else "backups/vector_db/vector_db_latest.tar.gz"
    else:
        # Use specific timestamp
        db_key = f"backups/{instance_id}/database/insightshop_{backup_type}.db" if instance_id else f"backups/database/insightshop_{backup_type}.db"
        vector_key = f"backups/{instance_id}/vector_db/vector_db_{backup_type}.tar.gz" if instance_id else f"backups/vector_db/vector_db_{backup_type}.tar.gz"
    
    logger.warning("⚠️  This will overwrite existing databases!")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Restore cancelled.")
        return False
    
    db_success = restore_database(s3_client, bucket_name, db_key, instance_id)
    vector_success = restore_chromadb(s3_client, bucket_name, vector_key, instance_id)
    
    if db_success and vector_success:
        logger.info("✅ Restore completed successfully!")
        return True
    else:
        logger.error("❌ Restore failed. Check logs above.")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

