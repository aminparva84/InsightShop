"""
Migrate AI assistant to 3 fixed providers (OpenAI, Gemini, Anthropic). Bedrock has been removed.
- Adds columns to ai_assistant_configs: source, is_valid, last_tested_at, sdk (if missing).
- Creates ai_selected_provider table and seeds provider='auto'.
- Ensures exactly 3 rows in ai_assistant_configs (one per provider).
Run once: python scripts/migrate_ai_four_providers.py
"""
import sqlite3
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv('DB_PATH', 'insightshop.db')
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(_root, DB_PATH)
if not os.path.exists(DB_PATH) and os.path.exists(os.path.join(_root, 'instance', 'insightshop.db')):
    DB_PATH = os.path.join(_root, 'instance', 'insightshop.db')

PROVIDERS = [
    ('openai', 'OpenAI', 'REST API'),
    ('gemini', 'Google Gemini', 'REST API'),
    ('anthropic', 'Anthropic', 'REST API'),
]


def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Add columns to ai_assistant_configs if missing
    cur.execute("PRAGMA table_info(ai_assistant_configs)")
    columns = [row[1] for row in cur.fetchall()]
    for col, default, col_type in [
        ('source', "'env'", 'VARCHAR(20)'),
        ('is_valid', '0', 'BOOLEAN'),
        ('last_tested_at', 'NULL', 'DATETIME'),
        ('sdk', 'NULL', 'VARCHAR(64)'),
        ('latency_ms', 'NULL', 'INTEGER'),
    ]:
        if col not in columns:
            cur.execute(f"ALTER TABLE ai_assistant_configs ADD COLUMN {col} {col_type} DEFAULT {default}")
            print(f"Added column {col}")
    # Ensure provider is unique (sqlite may not have unique constraint)
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_assistant_configs_provider ON ai_assistant_configs(provider)")
    except Exception:
        pass

    # Create ai_selected_provider table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_selected_provider (
            id INTEGER NOT NULL PRIMARY KEY,
            provider VARCHAR(20) NOT NULL DEFAULT 'auto',
            updated_at DATETIME
        )
    """)
    cur.execute("SELECT COUNT(*) FROM ai_selected_provider")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO ai_selected_provider (id, provider, updated_at) VALUES (1, 'auto', datetime('now'))")
        print("Seeded ai_selected_provider with provider='auto'")

    # Get existing providers
    cur.execute("SELECT id, provider FROM ai_assistant_configs")
    existing = {row[1]: row[0] for row in cur.fetchall()}

    for provider, name, sdk in PROVIDERS:
        if provider in existing:
            cur.execute(
                "UPDATE ai_assistant_configs SET name = ?, sdk = ?, source = COALESCE(source, 'env'), is_valid = COALESCE(is_valid, 0) WHERE provider = ?",
                (name, sdk, provider)
            )
        else:
            # is_active exists in legacy schema (NOT NULL); include it for new rows
            cur.execute("PRAGMA table_info(ai_assistant_configs)")
            cols = [row[1] for row in cur.fetchall()]
            if 'is_active' in cols:
                cur.execute(
                    """INSERT INTO ai_assistant_configs (provider, name, sdk, source, is_valid, is_active, created_at, updated_at)
                       VALUES (?, ?, ?, 'env', 0, 1, datetime('now'), datetime('now'))""",
                    (provider, name, sdk)
                )
            else:
                cur.execute(
                    """INSERT INTO ai_assistant_configs (provider, name, sdk, source, is_valid, created_at, updated_at)
                       VALUES (?, ?, ?, 'env', 0, datetime('now'), datetime('now'))""",
                    (provider, name, sdk)
                )
            print(f"Inserted provider row: {provider}")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == '__main__':
    main()
