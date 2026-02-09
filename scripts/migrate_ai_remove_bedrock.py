"""
Remove AWS Bedrock from AI assistant and ensure 3 providers (OpenAI, Gemini, Anthropic).
- Adds latency_ms to ai_assistant_configs if missing.
- Deletes any ai_assistant_configs row where provider='bedrock'.
- Sets ai_selected_provider.provider='auto' where it was 'bedrock'.
- Ensures rows exist for openai, gemini, anthropic (same as migrate_ai_four_providers).
Run once: python scripts/migrate_ai_remove_bedrock.py
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

    # Ensure ai_assistant_configs exists and has latency_ms
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_assistant_configs'")
    if cur.fetchone():
        cur.execute("PRAGMA table_info(ai_assistant_configs)")
        columns = [row[1] for row in cur.fetchall()]
        if 'latency_ms' not in columns:
            cur.execute("ALTER TABLE ai_assistant_configs ADD COLUMN latency_ms INTEGER")
            print("Added column latency_ms to ai_assistant_configs")
        for col, default, col_type in [
            ('source', "'env'", 'VARCHAR(20)'),
            ('is_valid', '0', 'BOOLEAN'),
            ('last_tested_at', 'NULL', 'DATETIME'),
            ('sdk', 'NULL', 'VARCHAR(64)'),
        ]:
            if col not in columns:
                cur.execute(f"ALTER TABLE ai_assistant_configs ADD COLUMN {col} {col_type} DEFAULT {default}")
                print(f"Added column {col}")
        columns = [row[1] for row in cur.execute("PRAGMA table_info(ai_assistant_configs)").fetchall()]

        # Remove Bedrock: delete config row
        cur.execute("DELETE FROM ai_assistant_configs WHERE provider = 'bedrock'")
        if cur.rowcount:
            print(f"Removed {cur.rowcount} Bedrock config row(s) from ai_assistant_configs")

    # ai_selected_provider: set 'bedrock' -> 'auto'
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_selected_provider'")
    if cur.fetchone():
        cur.execute("UPDATE ai_selected_provider SET provider = 'auto' WHERE provider = 'bedrock'")
        if cur.rowcount:
            print("Reset selected provider from 'bedrock' to 'auto'")
    else:
        cur.execute("""
            CREATE TABLE ai_selected_provider (
                id INTEGER NOT NULL PRIMARY KEY,
                provider VARCHAR(20) NOT NULL DEFAULT 'auto',
                updated_at DATETIME
            )
        """)
        cur.execute("INSERT INTO ai_selected_provider (id, provider, updated_at) VALUES (1, 'auto', datetime('now'))")
        print("Created ai_selected_provider with provider='auto'")

    # Ensure 3 provider rows exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_assistant_configs'")
    if cur.fetchone():
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_assistant_configs_provider ON ai_assistant_configs(provider)")
        cur.execute("SELECT id, provider FROM ai_assistant_configs")
        existing = {row[1]: row[0] for row in cur.fetchall()}
        cur.execute("PRAGMA table_info(ai_assistant_configs)")
        cols = [row[1] for row in cur.fetchall()]

        for provider, name, sdk in PROVIDERS:
            if provider in existing:
                cur.execute(
                    "UPDATE ai_assistant_configs SET name = ?, sdk = ?, source = COALESCE(source, 'env'), is_valid = COALESCE(is_valid, 0) WHERE provider = ?",
                    (name, sdk, provider)
                )
            else:
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
    print("Migration done.")


if __name__ == '__main__':
    main()
