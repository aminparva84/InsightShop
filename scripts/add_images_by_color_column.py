"""
Add images_by_color column to products table for color-specific product images.
Run once: python -m scripts.add_images_by_color_column

Uses the app's database config. Safe to run multiple times (skips if column exists).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_images_by_color_column():
    from app import app
    from models.database import db
    from sqlalchemy import text

    with app.app_context():
        try:
            conn = db.engine.connect()
            dialect_name = db.engine.dialect.name
            if dialect_name == 'sqlite':
                cursor = conn.execute(text("PRAGMA table_info(products)"))
                cols = [row[1] for row in cursor]
                if 'images_by_color' not in cols:
                    conn.execute(text("ALTER TABLE products ADD COLUMN images_by_color TEXT"))
                    conn.commit()
                    print("[OK] Added column products.images_by_color (SQLite)")
                else:
                    print("[OK] Column products.images_by_color already exists")
            elif dialect_name == 'postgresql':
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'products' AND column_name = 'images_by_color'
                        ) THEN
                            ALTER TABLE products ADD COLUMN images_by_color TEXT;
                        END IF;
                    END $$;
                """))
                conn.commit()
                print("[OK] Added column products.images_by_color if missing (PostgreSQL)")
            else:
                print(f"[WARN] Unknown dialect {dialect_name}; add column manually: ALTER TABLE products ADD COLUMN images_by_color TEXT;")
            conn.close()
        except Exception as e:
            print(f"[ERROR] {e}")
            raise

if __name__ == '__main__':
    add_images_by_color_column()
