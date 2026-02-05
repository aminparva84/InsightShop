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
        from models.review import Review
        try:
            from models.sale import Sale
        except ImportError:
            print("Warning: Sale model not found, sales feature will be disabled")
            Sale = None
        try:
            from models.product_relation import ProductRelation
        except ImportError:
            print("Warning: ProductRelation model not found, product relations feature will be disabled")
            ProductRelation = None
        try:
            from models.return_model import Return
        except ImportError:
            print("Warning: Return model not found, returns feature will be disabled")
            Return = None
        try:
            from models.shipment import Shipment
        except ImportError:
            print("Warning: Shipment model not found, shipment tracking feature will be disabled")
            Shipment = None
        try:
            from models.ai_assistant_config import AiAssistantConfig, AISelectedProvider
        except ImportError:
            print("Warning: AiAssistantConfig model not found, AI assistant admin feature will be disabled")
            AiAssistantConfig = None
            AISelectedProvider = None

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

        # Add Order.currency column if missing (existing databases)
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                if db.engine.dialect.name == 'sqlite':
                    cursor = conn.execute(text("PRAGMA table_info(orders)"))
                    columns = [row[1] for row in cursor.fetchall()]
                    if 'currency' not in columns:
                        conn.execute(text("ALTER TABLE orders ADD COLUMN currency VARCHAR(10) DEFAULT 'USD'"))
                        conn.commit()
                        print("[OK] Added column orders.currency for existing database")
        except Exception as e:
            print(f"[WARNING] Could not add orders.currency column: {e}")

        # Add Product.season column if missing (existing databases); backfill NULLs to all_season
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                if db.engine.dialect.name == 'sqlite':
                    cursor = conn.execute(text("PRAGMA table_info(products)"))
                    columns = [row[1] for row in cursor.fetchall()]
                    if 'season' not in columns:
                        conn.execute(text("ALTER TABLE products ADD COLUMN season VARCHAR(20) DEFAULT 'all_season'"))
                        conn.commit()
                        print("[OK] Added column products.season for existing database")
                    # Ensure every product has a season (backfill NULLs)
                    conn.execute(text("UPDATE products SET season = 'all_season' WHERE season IS NULL OR season = ''"))
                    conn.commit()
        except Exception as e:
            print(f"[WARNING] Could not add/backfill products.season column: {e}")

        # Add Product.clothing_category column if missing (existing databases); backfill to 'other'
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                if db.engine.dialect.name == 'sqlite':
                    cursor = conn.execute(text("PRAGMA table_info(products)"))
                    columns = [row[1] for row in cursor.fetchall()]
                    if 'clothing_category' not in columns:
                        conn.execute(text("ALTER TABLE products ADD COLUMN clothing_category VARCHAR(50) DEFAULT 'other'"))
                        conn.commit()
                        print("[OK] Added column products.clothing_category for existing database")
                    conn.execute(text("UPDATE products SET clothing_category = 'other' WHERE clothing_category IS NULL OR clothing_category = ''"))
                    conn.commit()
        except Exception as e:
            print(f"[WARNING] Could not add/backfill products.clothing_category column: {e}")
        
        # Verify Sale table was created
        try:
            # Try a simple query to verify table exists
            try:
                Sale.query.limit(1).all()
                print("[OK] Sales table verified")
            except Exception as e:
                print(f"[WARNING] Sales table may not exist: {e}")
                # Try to create it explicitly
                try:
                    Sale.__table__.create(db.engine, checkfirst=True)
                    print("[OK] Sales table created")
                except Exception as e2:
                    print(f"[WARNING] Could not create Sales table: {e2}")
        except Exception as e:
            print(f"[WARNING] Could not verify Sales table: {e}")
        
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

