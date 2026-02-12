# Using PostgreSQL (SQLite to PostgreSQL migration)

InsightShop uses **SQLite** by default. You can switch to **PostgreSQL** at any time by setting `DATABASE_URL`. The app and migrations work with both backends.

## Quick switch to PostgreSQL

1. **Install the driver** (if not already installed):
   ```bash
   pip install psycopg2-binary
   ```

2. **Create a PostgreSQL database** (local or managed, e.g. AWS RDS, Neon, Supabase).

3. **Set the connection URL** in your environment or `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```
   For SSL (e.g. cloud Postgres):
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
   ```

4. **Start the app**. On first run with PostgreSQL, the app will:
   - Create all tables (`db.create_all()`)
   - Run optional column backfills (e.g. `orders.currency`, `products.season`) if tables already existed

5. **Optional: use Flask-Migrate for schema versioning**
   - One-time setup:
     ```bash
     export FLASK_APP=app.py   # Windows: set FLASK_APP=app.py
     flask db init            # already done if migrations/ exists
     flask db migrate -m "Initial schema"
     flask db upgrade
     ```
   - For future schema changes: edit models, then `flask db migrate -m "description"` and `flask db upgrade`.

## Switching back to SQLite

- **Unset** `DATABASE_URL` (remove it from `.env` or set it to empty).
- The app will use `DB_PATH` (default `insightshop.db`) under the `instance/` folder.

## Data migration (SQLite → PostgreSQL)

To **move existing data** from SQLite to PostgreSQL:

1. **Option A – pgloader (recommended)**  
   Install [pgloader](https://pgloader.io/) and run:
   ```bash
   pgloader insightshop.db postgresql://user:password@host:5432/dbname
   ```
   Then point the app at PostgreSQL with `DATABASE_URL` and run any migrations if you use Flask-Migrate.

2. **Option B – Export/import**  
   Use your own scripts to export from SQLite (e.g. CSV or SQL dump) and import into PostgreSQL, then set `DATABASE_URL`.

3. **Option C – Fresh start**  
   Set `DATABASE_URL` to a new empty PostgreSQL database. The app will create tables and seed products/users as on first run (no existing SQLite data is copied).

## Configuration reference

| Variable       | Purpose |
|----------------|--------|
| `DATABASE_URL` | If set, used as `SQLALCHEMY_DATABASE_URI` (e.g. PostgreSQL). When empty, SQLite is used. |
| `DB_PATH`      | Used only when `DATABASE_URL` is not set; SQLite file path (default `insightshop.db`, relative to `instance/`). |

PostgreSQL engine options (pool) are set automatically when `DATABASE_URL` is used (`pool_pre_ping`, `pool_size`, `max_overflow`).

## Troubleshooting

- **Connection refused**: Check host, port (5432), and firewall/security groups.
- **Authentication failed**: Verify user and password in `DATABASE_URL`; for managed Postgres, use the provided connection string.
- **SSL required**: Append `?sslmode=require` to `DATABASE_URL`.
- **Tables already exist**: The app and migrations are idempotent; safe to run against an existing DB.
