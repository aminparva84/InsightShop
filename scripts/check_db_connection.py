#!/usr/bin/env python3
"""
Verify database path and connection. Run from project root when the DB connection is severed.

Usage:
  python scripts/check_db_connection.py

Checks:
  - DB_PATH from env / .env
  - Resolved path (instance/insightshop.db by default)
  - Directory exists, file exists or can be created
  - Simple SELECT 1 connection test
"""
import os
import sys

# Project root = parent of scripts/
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

# Load .env before config
from dotenv import load_dotenv
load_dotenv(os.path.join(_root, '.env'))

db_path_env = os.getenv('DB_PATH', 'insightshop.db')
instance_dir = os.path.join(_root, 'instance')
if os.path.isabs(db_path_env):
    resolved_path = db_path_env
else:
    resolved_path = os.path.join(instance_dir, db_path_env)

print("Database connection check")
print("=" * 50)
print(f"  DB_PATH (env):    {db_path_env!r}")
print(f"  Resolved path:    {os.path.abspath(resolved_path)}")
print(f"  Instance dir:     {instance_dir}")
print(f"  Instance exists: {os.path.isdir(instance_dir)}")
print(f"  DB file exists:   {os.path.isfile(resolved_path)}")
print()

# Ensure directory exists
db_dir = os.path.dirname(resolved_path)
if db_dir and not os.path.exists(db_dir):
    print(f"  Creating directory: {db_dir}")
    os.makedirs(db_dir, exist_ok=True)

# Try connection using the app's db (same as running server)
try:
    from app import app, db
    with app.app_context():
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        print("  Connection test:  OK")
        print()
        print("If the app still fails, restart the Flask server so it picks up the same path.")
except Exception as e:
    print(f"  Connection test:  FAILED")
    print(f"  Error: {e}")
    print()
    print("Suggestions:")
    print("  1. Ensure no other process is locking the DB file (e.g. another Flask run).")
    print("  2. In .env set DB_PATH=insightshop.db (relative) so the file is under instance/.")
    print("  3. If you use AWS Secrets Manager, ensure the secret does not override DB_PATH with a remote path when running locally.")
    sys.exit(1)
