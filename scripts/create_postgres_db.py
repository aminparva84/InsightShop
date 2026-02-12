"""
Create a PostgreSQL database if it does not exist.
Usage: python scripts/create_postgres_db.py
Reads DATABASE_URL from environment (or .env). Example:
  DATABASE_URL=postgresql://postgres:1234@localhost:5432/Insightshop
Creates the database named in the URL (e.g. Insightshop) by connecting to 'postgres' first.
"""
import os
import sys

# Project root
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv
load_dotenv(os.path.join(_root, ".env"))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from psycopg2 import sql
except ImportError:
    print("Install psycopg2-binary: pip install psycopg2-binary")
    sys.exit(1)

def main():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url or not url.startswith("postgresql"):
        print("Set DATABASE_URL (e.g. postgresql://user:pass@host:5432/dbname)")
        sys.exit(1)

    # Parse URL to get host, port, user, password, dbname (simple parse)
    # postgresql://user:password@host:5432/dbname
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    user = parsed.username or "postgres"
    password = parsed.password or ""
    dbname = (parsed.path or "").strip("/") or "postgres"

    if dbname == "postgres":
        print("DATABASE_URL must point to a specific database name, not 'postgres'")
        sys.exit(1)

    # Connect to default 'postgres' database to create the target DB
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if database exists (case-sensitive; PostgreSQL stores unquoted names as lowercase)
    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (dbname,),
    )
    if cur.fetchone():
        print(f"Database {dbname!r} already exists.")
        cur.close()
        conn.close()
        return

    # Create database (quote name to preserve case if mixed)
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    print(f"Created database {dbname!r}.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
