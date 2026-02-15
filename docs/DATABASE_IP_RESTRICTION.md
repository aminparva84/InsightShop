# Restrict Database Access to a Single IP (18.193.0.149)

Only the IP **18.193.0.149** should be able to connect to your PostgreSQL database (e.g. for DBeaver or admin tools). The app itself must also be allowed if it runs on a different host.

## Allowed IP

| Purpose | IP |
|--------|---|
| DBeaver / DB admin only | **18.193.0.149** |

If your **InsightShop app** runs on another server (e.g. EC2, ECS), you must allow that server’s IP or security group as well, or the app will lose DB access.

---

## AWS RDS PostgreSQL

Restrict access using a **security group** that allows only the allowed IP(s) on port 5432.

### Option A: Script (recommended)

Use the project script to create a security group that allows only **18.193.0.149** on port 5432, then attach it to your RDS instance:

```bash
# From project root (requires AWS CLI configured)
python scripts/aws_db_security_group_allow_ip.py
```

You must pass your **VPC ID** (same VPC as RDS). Optionally attach the new SG to your RDS instance:

```bash
python scripts/aws_db_security_group_allow_ip.py --vpc-id vpc-xxxxxxxxx --attach-rds your-db-instance-id
```

If you omit `--attach-rds`, attach the created security group manually: **RDS → your DB → Modify → Security group** (add the new SG). Ensure the **app** can still reach the DB (keep the app’s SG on the RDS instance or allow the app’s IP in the same SG).

### Option B: Manual in AWS Console

1. **EC2 → Security Groups → Create security group**
   - Name: e.g. `insightshop-db-admin-only`
   - VPC: same as your RDS instance
   - **Inbound rules:**
     - Type: **PostgreSQL**
     - Port: **5432**
     - Source: **18.193.0.149/32**
   - Create.

2. **RDS → Databases → your DB → Modify**
   - Under **Connectivity**, set **Security group** to the new group (or add it in addition to the one used by the app).
   - If the app runs in the same VPC and uses a different SG, keep that SG on the RDS instance so the app can connect, and add the new SG so 18.193.0.149 can connect for DBeaver.

3. **If the app and DBeaver must both connect:**
   - Use one SG with two rules:  
     - 5432 from **18.193.0.149/32** (DBeaver)  
     - 5432 from the **app’s security group** or **app’s IP** (so the app can connect).

### Option C: AWS CLI (one-off)

```bash
# Create SG (use your VPC ID)
aws ec2 create-security-group \
  --group-name insightshop-db-admin-only \
  --description "PostgreSQL access only from 18.193.0.149" \
  --vpc-id vpc-xxxxxxxxx

# Allow only 18.193.0.149 on 5432 (use the GroupId from previous output)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 5432 \
  --cidr 18.193.0.149/32
```

Then attach this security group to your RDS instance (Console or `aws rds modify-db-instance --db-instance-identifier your-db-id --vpc-security-group-ids sg-xxxxxxxxx ...`).

---

## Self-hosted PostgreSQL (pg_hba.conf)

On the server where PostgreSQL runs, edit `pg_hba.conf` (e.g. `/etc/postgresql/14/main/pg_hba.conf` or `/var/lib/pgsql/data/pg_hba.conf`) so that only 18.193.0.149 (and optionally the app host) can connect.

Example (replace with your actual DB name and user if needed):

```text
# TYPE  DATABASE        USER            ADDRESS             METHOD
# Allow only 18.193.0.149 for all DBs (e.g. DBeaver)
host    all             all             18.193.0.149/32     scram-sha-256
# Allow app server (example: 10.0.1.5 in same VPC)
host    all             all             10.0.1.5/32          scram-sha-256
# Deny others (optional; default may be reject)
# host   all             all             0.0.0.0/0            reject
```

Then reload PostgreSQL:

```bash
sudo systemctl reload postgresql
# or: psql -U postgres -c "SELECT pg_reload_conf();"
```

---

## Neon / Supabase / other managed Postgres

- **Neon**: Project **Settings → Security → Allowed IP addresses** (or “Restrict connections”). Add **18.193.0.149** and remove or avoid “Allow all” so only this IP can connect. Ensure the app’s IP is allowed if it runs elsewhere.
- **Supabase**: **Project Settings → Database → Connection string**; use **Restrict connections** / **Network** and add **18.193.0.149** (and the app IP if needed).

---

## Summary

| Where DB runs        | How to allow only 18.193.0.149                          |
|----------------------|----------------------------------------------------------|
| **AWS RDS**          | Security group: allow 5432 from **18.193.0.149/32** (and app SG if needed). |
| **Self-hosted**      | `pg_hba.conf`: allow **18.193.0.149/32** (and app host). |
| **Neon / Supabase**  | Dashboard: add **18.193.0.149** to allowed IPs.          |

After changing rules, test from 18.193.0.149 (e.g. DBeaver) and from the app host to confirm both work.
