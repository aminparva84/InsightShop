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
        from models.payment_log import PaymentLog
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

        # Create database directory from app's actual DB path (e.g. instance/insightshop.db)
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if uri.startswith('sqlite:///'):
            db_file_path = uri.replace('sqlite:///', '').replace('/', os.sep)
            db_dir = os.path.dirname(db_file_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        
        # Only delete database if explicitly needed (commented out to preserve data)
        # if os.path.exists(Config.DB_PATH):
        #     os.remove(Config.DB_PATH)
        #     print(f"Existing database '{Config.DB_PATH}' removed to apply schema updates.")
        
        # Create all tables with new schema
        db.create_all()
        _log_path = uri.replace('sqlite:///', '').replace('/', os.sep) if uri.startswith('sqlite:///') else Config.DB_PATH
        print(f"Database tables created at: {_log_path}")
        # Verify connection so "severed" state is detected at startup
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("[DB] Connection verified.")
        except Exception as e:
            print(f"[DB] ERROR: Connection failed: {e}")
            print(f"      Check that the file exists and is not locked: {_log_path}")

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

        # Add User.is_superadmin column if missing (existing databases)
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                if db.engine.dialect.name == 'sqlite':
                    cursor = conn.execute(text("PRAGMA table_info(users)"))
                    columns = [row[1] for row in cursor.fetchall()]
                    if 'is_superadmin' not in columns:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN DEFAULT 0"))
                        conn.commit()
                        print("[OK] Added column users.is_superadmin for existing database")
        except Exception as e:
            print(f"[WARNING] Could not add users.is_superadmin column: {e}")

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

        # Seed superadmin and demo users so admin can manage the app (production / App Runner)
        if not app.config.get('TESTING'):
            try:
                from scripts.seed_users import run_seed_users
                run_seed_users(app)
            except Exception as e:
                print(f"Warning: Could not seed users (superadmin): {e}")

        # Defer vector DB sync to a background thread so the app can bind and pass health check (e.g. App Runner).
        # Sync runs after startup; ONNX/Chroma can be slow or fail in minimal containers.
        if not app.config.get('TESTING'):
            import threading
            def _deferred_sync():
                try:
                    from utils.vector_db import sync_all_products_from_sql
                    sync_all_products_from_sql(app)
                except Exception as e:
                    print(f"Warning: Could not sync products to vector DB: {e}")
            threading.Thread(target=_deferred_sync, daemon=True).start()
        
        if not app.config.get('TESTING'):
            print("Database initialized successfully!")

