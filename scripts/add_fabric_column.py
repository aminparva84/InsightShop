"""Add fabric column to products table."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
import sqlite3

def add_fabric_column():
    """Add fabric column to products table if it doesn't exist."""
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if column exists
            cursor.execute("PRAGMA table_info(products)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'fabric' not in columns:
                print("Adding fabric column to products table...")
                cursor.execute("ALTER TABLE products ADD COLUMN fabric VARCHAR(100)")
                conn.commit()
                print("Fabric column added successfully!")
            else:
                print("Fabric column already exists.")
        except Exception as e:
            print(f"Error adding fabric column: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    add_fabric_column()

