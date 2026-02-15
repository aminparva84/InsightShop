# Connecting DBeaver to InsightShop PostgreSQL (Deployed)

Use DBeaver to connect to the PostgreSQL database used by your **deployed** InsightShop instance.

## 1. Connection URL (replace HOST and DATABASE)

The project uses this URL format (see `env.docker.example`):

```text
postgresql://postgres:1234@HOST:5432/DATABASE
```

**You only need to replace:**

- **HOST** — your Postgres server (e.g. `your-db.region.rds.amazonaws.com` or `db.xxx.neon.tech`)
- **DATABASE** — your database name (e.g. `insightshop`)

Then use the same values in DBeaver:

| DBeaver field | Value |
|---------------|--------|
| **Host**      | Whatever you put for HOST |
| **Port**      | `5432` |
| **Database**  | Whatever you put for DATABASE |
| **Username**  | `postgres` |
| **Password**  | `1234` |

For cloud Postgres, add SSL: use `?sslmode=require` on the URL and in DBeaver enable **SSL** and set mode to **require** (see section 4).

---

## 2. Create a new connection in DBeaver

1. Open **DBeaver**.
2. **Database → New Database Connection** (or click the plug icon).
3. Choose **PostgreSQL** → **Next**.

---

## 3. Main tab

- **Host**: your HOST (e.g. RDS endpoint or Neon host).
- **Port**: `5432`.
- **Database**: your DATABASE name.
- **Username**: `postgres`.
- **Password**: `1234`.

Click **Test Connection**. If DBeaver asks to download the PostgreSQL driver, allow it.

---

## 4. If your provider requires SSL

Many hosted Postgres services (AWS RDS, Neon, Supabase, etc.) require SSL:

1. In the connection dialog, open the **SSL** tab.
2. Enable **Use SSL**.
3. Set **SSL mode** to **require** (or **verify-full** if you have a CA certificate).
4. Test the connection again.

---

## 5. Firewall / network

- **Cloud Postgres (RDS, Neon, etc.)**: Ensure your IP (or your office/VPN) is allowed in the database’s firewall / security group / “allowed IPs” so DBeaver can reach the host.
- **Self-hosted / VPC**: You may need VPN or SSH tunnel to reach the DB; configure that before or in DBeaver (e.g. SSH tunnel in the connection settings).

---

## 6. Security

- Prefer **saving the password in DBeaver’s secure storage** rather than sharing it.
- Do **not** commit `.env` or screenshots containing `DATABASE_URL` to git.
- Use a DB user with only the rights you need (e.g. read-only for analytics, or full for admin).

---

## Quick reference (this project)

```text
postgresql://postgres:1234@HOST:5432/DATABASE
```

- Host: **HOST** (replace with your server)
- Port: **5432**
- Database: **DATABASE** (replace with your db name)
- Username: **postgres**
- Password: **1234**

Use these in DBeaver. If your provider needs SSL, add `?sslmode=require` to the URL and enable SSL in DBeaver (SSL tab).
