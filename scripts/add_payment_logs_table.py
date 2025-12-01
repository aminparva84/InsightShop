"""
Script to add payment_logs table to the database.
Run this script to create the payment_logs table for logging all payment attempts.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set encoding to avoid Unicode issues
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from models.database import db, init_db
from models.payment_log import PaymentLog

def add_payment_logs_table():
    """Create the payment_logs table."""
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/insightshop.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("[OK] Payment logs table created successfully!")
            print(f"[OK] Table name: {PaymentLog.__tablename__}")
            print("\nPayment logs table is ready to use.")
            print("All payment attempts will now be logged automatically.")
        except Exception as e:
            print(f"[ERROR] Error creating payment logs table: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    add_payment_logs_table()

