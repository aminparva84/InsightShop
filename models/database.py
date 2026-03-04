from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()


def ensure_postgres_database(uri):
    """
    If URI is PostgreSQL, ensure the target database exists by connecting to
    the 'postgres' database and creating it if missing. No-op for non-PostgreSQL URIs.
    """
    if not uri or not uri.strip().lower().startswith("postgresql"):
        return
    from urllib.parse import urlparse, urlunparse
    from sqlalchemy import create_engine, text

    parsed = urlparse(uri)
    path = (parsed.path or "/").lstrip("/")
    # path may be "dbname" or "dbname?sslmode=require"
    dbname = path.split("?")[0].strip() or "postgres"
    if dbname == "postgres":
        return
    if not all(c.isalnum() or c == "_" for c in dbname):
        return
    # Build URI pointing to 'postgres' database so we can run CREATE DATABASE
    netloc = parsed.netloc or ""
    query = "?" + parsed.query if parsed.query else ""
    admin_path = "/postgres" + query
    admin_uri = urlunparse((parsed.scheme, netloc, admin_path, parsed.params, "", ""))
    engine = None
    try:
        engine = create_engine(admin_uri, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            row = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": dbname}).fetchone()
            if row is None:
                conn.execute(text('CREATE DATABASE "' + dbname.replace('"', '""') + '"'))
                print(f"[DB] Created PostgreSQL database: {dbname}")
    except Exception as e:
        print(f"[DB] Could not ensure database {dbname!r}: {e}")
    finally:
        if engine is not None:
            engine.dispose()


def _table_has_column(connection, table_name, column_name, dialect_name):
    """Return True if the table has the column. Works with SQLite and PostgreSQL."""
    from sqlalchemy import text
    if dialect_name == 'sqlite':
        # PRAGMA in SQLite does not support bound params; table_name is from our code only
        cursor = connection.execute(text(f"PRAGMA table_info({table_name!r})"))
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    if dialect_name == 'postgresql':
        cursor = connection.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c LIMIT 1"
            ),
            {"t": table_name, "c": column_name}
        )
        return cursor.fetchone() is not None
    return False


def init_db(app):
    """Initialize the database and create tables."""
    db.init_app(app)
    
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        from models.user import User
        from models.product import Product
        from models.product_variation import ProductVariation
        from models.cart import CartItem
        from models.wishlist import WishlistItem
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
        if uri.startswith('sqlite:///'):
            _log_path = uri.replace('sqlite:///', '').replace('/', os.sep)
        else:
            _log_path = uri.split('@')[-1] if '@' in uri else uri  # e.g. host/db for postgres
        print(f"Database tables created: {_log_path}")
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
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'orders', 'currency', dialect_name):
                    conn.execute(text("ALTER TABLE orders ADD COLUMN currency VARCHAR(10) DEFAULT 'USD'"))
                    conn.commit()
                    print("[OK] Added column orders.currency for existing database")
        except Exception as e:
            print(f"[WARNING] Could not add orders.currency column: {e}")

        # Add Product.season column if missing (existing databases); backfill NULLs to all_season
        try:
            from sqlalchemy import text
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'products', 'season', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN season VARCHAR(20) DEFAULT 'all_season'"))
                    conn.commit()
                    print("[OK] Added column products.season for existing database")
                conn.execute(text("UPDATE products SET season = 'all_season' WHERE season IS NULL OR season = ''"))
                conn.commit()
        except Exception as e:
            print(f"[WARNING] Could not add/backfill products.season column: {e}")

        # Add Product.clothing_category column if missing (existing databases); backfill to 'other'
        try:
            from sqlalchemy import text
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'products', 'clothing_category', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN clothing_category VARCHAR(50) DEFAULT 'other'"))
                    conn.commit()
                    print("[OK] Added column products.clothing_category for existing database")
                conn.execute(text("UPDATE products SET clothing_category = 'other' WHERE clothing_category IS NULL OR clothing_category = ''"))
                conn.commit()
        except Exception as e:
            print(f"[WARNING] Could not add/backfill products.clothing_category column: {e}")

        # Add Product.brand and Product.brand_other columns if missing; backfill existing to 'other'
        try:
            from sqlalchemy import text
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'products', 'brand', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN brand VARCHAR(50) DEFAULT 'other'"))
                    conn.commit()
                    print("[OK] Added column products.brand for existing database")
                if not _table_has_column(conn, 'products', 'brand_other', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN brand_other VARCHAR(255)"))
                    conn.commit()
                    print("[OK] Added column products.brand_other for existing database")
                conn.execute(text("UPDATE products SET brand = 'other' WHERE brand IS NULL OR brand = ''"))
                conn.commit()
        except Exception as e:
            print(f"[WARNING] Could not add/backfill products.brand columns: {e}")

        # Add Product per-product sale columns if missing (sale_enabled, sale_start, sale_end, sale_percentage)
        try:
            from sqlalchemy import text
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'products', 'sale_enabled', dialect_name):
                    default_bool = "0" if dialect_name == 'sqlite' else "FALSE"
                    conn.execute(text(f"ALTER TABLE products ADD COLUMN sale_enabled BOOLEAN DEFAULT {default_bool}"))
                    conn.commit()
                    print("[OK] Added column products.sale_enabled")
                if not _table_has_column(conn, 'products', 'sale_start', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN sale_start DATE"))
                    conn.commit()
                    print("[OK] Added column products.sale_start")
                if not _table_has_column(conn, 'products', 'sale_end', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN sale_end DATE"))
                    conn.commit()
                    print("[OK] Added column products.sale_end")
                if not _table_has_column(conn, 'products', 'sale_percentage', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN sale_percentage NUMERIC(5,2)"))
                    conn.commit()
                    print("[OK] Added column products.sale_percentage")
        except Exception as e:
            print(f"[WARNING] Could not add product sale columns: {e}")

        # Add Product.size_stock column if missing (per-size quantity: JSON object)
        try:
            from sqlalchemy import text
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'products', 'size_stock', dialect_name):
                    conn.execute(text("ALTER TABLE products ADD COLUMN size_stock TEXT"))
                    conn.commit()
                    print("[OK] Added column products.size_stock for existing database")
        except Exception as e:
            print(f"[WARNING] Could not add products.size_stock column: {e}")

        # Add cart_items.variation_id if missing (FK to product_variations)
        try:
            from sqlalchemy import text
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'cart_items', 'variation_id', dialect_name):
                    if dialect_name == 'postgresql':
                        conn.execute(text("ALTER TABLE cart_items ADD COLUMN variation_id INTEGER REFERENCES product_variations(id)"))
                    else:
                        conn.execute(text("ALTER TABLE cart_items ADD COLUMN variation_id INTEGER"))
                    conn.commit()
                    print("[OK] Added column cart_items.variation_id for existing database")
        except Exception as e:
            print(f"[WARNING] Could not add cart_items.variation_id column: {e}")

        # Add User.is_superadmin column if missing (existing databases)
        try:
            from sqlalchemy import text
            dialect_name = db.engine.dialect.name
            with db.engine.connect() as conn:
                if not _table_has_column(conn, 'users', 'is_superadmin', dialect_name):
                    # PostgreSQL uses FALSE not 0 for BOOLEAN default
                    default_val = "0" if dialect_name == 'sqlite' else "FALSE"
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN DEFAULT {default_val}"))
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

        # Legacy special-offer product seeding disabled: main seed (seed_products) now includes
        # products with sale_percentage; no separate 5 products that overwrote images.

        # Seed superadmin and demo users so admin can manage the app (production / App Runner)
        if not app.config.get('TESTING'):
            try:
                from scripts.seed_users import run_seed_users
                run_seed_users(app)
            except Exception as e:
                print(f"Warning: Could not seed users (superadmin): {e}")

        # Defer vector DB sync to a background thread so the app can bind and pass health check (e.g. App Runner).
        # Sync runs after a short delay to avoid OOM: worker stays under memory limit until health check passes.
        if not app.config.get('TESTING'):
            import threading
            import time
            def _deferred_sync():
                time.sleep(8)  # Let gunicorn bind and first health check succeed before heavy vector sync
                try:
                    from utils.vector_db import sync_all_products_from_sql
                    synced, _ = sync_all_products_from_sql(app)
                    if synced > 0:
                        print(f"Vector DB: synced {synced} products.")
                except Exception as e:
                    print(f"Warning: Could not sync products to vector DB: {e}")
            threading.Thread(target=_deferred_sync, daemon=True).start()
        
        if not app.config.get('TESTING'):
            print("Database initialized successfully!")

