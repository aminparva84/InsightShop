from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()

def init_db(app):
    """Initialize the database and create tables."""
    db.init_app(app)
    
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        from models.user import User
        from models.product import Product
        from models.cart import CartItem
        from models.order import Order, OrderItem
        from models.payment import Payment
        
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(Config.DB_PATH) if os.path.dirname(Config.DB_PATH) else '.'
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Only delete database if explicitly needed (commented out to preserve data)
        # if os.path.exists(Config.DB_PATH):
        #     os.remove(Config.DB_PATH)
        #     print(f"Existing database '{Config.DB_PATH}' removed to apply schema updates.")
        
        # Create all tables with new schema
        db.create_all()
        print(f"Database tables created at: {Config.DB_PATH}")
        
        # Initialize vector database (skip in test mode)
        if not app.config.get('TESTING'):
            try:
                from utils.vector_db import init_vector_db
                init_vector_db()
            except Exception as e:
                print(f"Warning: Could not initialize vector database: {e}")
        
        # Seed products if database is empty (skip in test mode)
        if not app.config.get('TESTING'):
            try:
                if Product.query.count() == 0:
                    from scripts.seed_products import seed_products
                    seed_products()
                    print(f"Products seeded: {Product.query.count()} products in database")
                else:
                    print(f"Database already has {Product.query.count()} products")
            except Exception as e:
                print(f"Warning: Could not seed products: {e}")
        
        if not app.config.get('TESTING'):
            print("Database initialized successfully!")

