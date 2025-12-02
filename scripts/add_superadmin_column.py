"""Migration script to add is_superadmin column to users table."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.user import User

def add_superadmin_column():
    """Add is_superadmin column to users table if it doesn't exist."""
    with app.app_context():
        try:
            # Check if column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'is_superadmin' not in columns:
                print("Adding is_superadmin column to users table...")
                from sqlalchemy import text
                db.session.execute(text('ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN DEFAULT 0'))
                db.session.commit()
                print("[OK] is_superadmin column added successfully!")
            else:
                print("[OK] is_superadmin column already exists")
            
            # Create index if it doesn't exist
            indexes = [idx['name'] for idx in inspector.get_indexes('users')]
            if 'ix_users_is_superadmin' not in indexes:
                print("Creating index on is_superadmin column...")
                from sqlalchemy import text
                db.session.execute(text('CREATE INDEX ix_users_is_superadmin ON users(is_superadmin)'))
                db.session.commit()
                print("[OK] Index created successfully!")
            else:
                print("[OK] Index already exists")
            
            print("\nMigration completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = add_superadmin_column()
    if success:
        print("\n✅ Superadmin column migration completed!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

