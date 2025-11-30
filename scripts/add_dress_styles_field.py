"""Add dress_style/neckline field to products table."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
from sqlalchemy import text

def add_dress_style_field():
    """Add dress_style column to products table if it doesn't exist."""
    with app.app_context():
        try:
            # Check if column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('products')]
            
            if 'dress_style' not in columns:
                print("Adding dress_style column to products table...")
                db.session.execute(text("ALTER TABLE products ADD COLUMN dress_style VARCHAR(100)"))
                db.session.commit()
                print("[OK] dress_style column added successfully")
            else:
                print("[OK] dress_style column already exists")
                
            # Add index for better search performance
            indexes = [idx['name'] for idx in inspector.get_indexes('products')]
            if 'idx_dress_style' not in indexes:
                print("Adding index for dress_style...")
                db.session.execute(text("CREATE INDEX idx_dress_style ON products(dress_style)"))
                db.session.commit()
                print("[OK] Index added successfully")
            else:
                print("[OK] Index already exists")
                
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_dress_style_field()

