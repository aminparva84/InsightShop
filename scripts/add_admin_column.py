"""Migration script to add is_admin column to users table."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.user import User

def add_admin_column():
    """Add is_admin column to users table if it doesn't exist."""
    with app.app_context():
        try:
            # Check if column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'is_admin' not in columns:
                print("Adding is_admin column to users table...")
                db.engine.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
                db.session.commit()
                print("✓ is_admin column added successfully!")
            else:
                print("✓ is_admin column already exists")
            
            # Create index if it doesn't exist
            indexes = [idx['name'] for idx in inspector.get_indexes('users')]
            if 'ix_users_is_admin' not in indexes:
                print("Creating index on is_admin column...")
                db.engine.execute('CREATE INDEX ix_users_is_admin ON users(is_admin)')
                print("✓ Index created successfully!")
            else:
                print("✓ Index already exists")
            
            print("\nMigration completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = add_admin_column()
    sys.exit(0 if success else 1)

