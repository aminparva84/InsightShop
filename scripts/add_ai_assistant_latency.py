"""
Add latency_ms column to ai_assistant_configs and migrate provider 'bedrock' -> 'anthropic'.
Run once: python scripts/add_ai_assistant_latency.py
"""
import sqlite3
import os
import sys

# Default DB path; allow override via env. Flask often uses instance/insightshop.db
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv('DB_PATH', 'insightshop.db')
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(_root, DB_PATH)
if not os.path.exists(DB_PATH) and os.path.exists(os.path.join(_root, 'instance', 'insightshop.db')):
    DB_PATH = os.path.join(_root, 'instance', 'insightshop.db')


def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if latency_ms already exists
    cur.execute("PRAGMA table_info(ai_assistant_configs)")
    columns = [row[1] for row in cur.fetchall()]
    if 'latency_ms' not in columns:
        cur.execute("ALTER TABLE ai_assistant_configs ADD COLUMN latency_ms INTEGER")
        print("Added column latency_ms")
    else:
        print("Column latency_ms already exists")

    # Migrate bedrock -> anthropic (direct API; user will need to add Anthropic API key in admin)
    cur.execute("UPDATE ai_assistant_configs SET provider = 'anthropic' WHERE provider = 'bedrock'")
    if cur.rowcount:
        print(f"Updated {cur.rowcount} config(s) from provider 'bedrock' to 'anthropic'. Add your Anthropic API key in Admin → AI Assistant.")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == '__main__':
    main()
