"""Script to create the sales table in the database."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.sale import Sale

def create_sales_table():
    """Create the sales table if it doesn't exist."""
    with app.app_context():
        try:
            # Create all tables (this will create sales table if it doesn't exist)
            db.create_all()
            print("✅ Sales table created successfully!")
            
            # Verify it exists
            try:
                count = Sale.query.count()
                print(f"✅ Verified: Sales table exists with {count} records")
            except Exception as e:
                print(f"⚠️ Warning: Could not verify sales table: {e}")
                
        except Exception as e:
            print(f"❌ Error creating sales table: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_sales_table()


