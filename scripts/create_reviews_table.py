"""Create reviews table for product reviews and ratings."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.review import Review

def create_reviews_table():
    """Create the reviews table if it doesn't exist."""
    with app.app_context():
        try:
            # Create the table
            Review.__table__.create(db.engine, checkfirst=True)
            print("✅ Reviews table created successfully!")
            
            # Verify it was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'reviews' in inspector.get_table_names():
                print("✅ Reviews table verified in database")
            else:
                print("⚠️ Warning: Reviews table not found after creation")
        except Exception as e:
            print(f"❌ Error creating reviews table: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_reviews_table()

