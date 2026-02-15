# Deploy PostgreSQL for InsightShop on AWS App Runner

This guide sets up **Amazon RDS PostgreSQL** and connects it to your **App Runner** service so the app uses PostgreSQL instead of SQLite. App Runner reaches RDS via a **VPC connector** (private subnets).

## Architecture

- **RDS PostgreSQL** in a **private subnet** (same VPC as the VPC connector).
- **App Runner VPC connector** in **private subnets** so outbound traffic to RDS goes through your VPC.
- **Security group on RDS**: allow port 5432 from the VPC connector (and optionally **18.193.0.149** for DBeaver).
- **App Runner service**: has `DATABASE_URL` set and uses the VPC connector for egress.

## Prerequisites

- AWS CLI configured (e.g. `aws configure`) in **us-east-1** (or your App Runner region).
- Existing App Runner service (e.g. created by the [deploy-apprunner](deploy-apprunner.md) workflow).
- A **VPC with private subnets**. If you use the default VPC, create **private subnets** and a **NAT gateway** (or use a custom VPC that already has them).

---

## Option A: Automated script (recommended)

From the project root (PowerShell, AWS CLI configured). **Only the database password is required**; the script uses the default VPC and its first two subnets if you don't pass `-VpcId` or `-SubnetIds`.

```powershell
.\scripts\setup-apprunner-postgres.ps1 -DbPassword "YourSecurePassword123"
```

Optional: use a specific VPC and subnets (e.g. private subnets):

```powershell
.\scripts\setup-apprunner-postgres.ps1 -DbPassword "YourSecurePassword123" -VpcId vpc-xxxx -SubnetIds "subnet-aaa,subnet-bbb"
```

The script will:

1. **Auto-discover** default VPC and two subnets (or use the ones you pass).
2. Create a **DB subnet group** and **security groups** (RDS: 5432 from VPC + 18.193.0.149; connector SG).
3. Create **RDS PostgreSQL** (db.t3.micro, single-AZ).
4. Create an **App Runner VPC connector**.
5. Print **DATABASE_URL** and **VpcConnectorArn**.

You then:

- Add **DATABASE_URL** to the App Runner service (Configuration → Environment variables, or [GitHub secret](#optional-database_url-in-github-actions)).
- Set **Networking → Outgoing traffic → VPC connector** to the new connector.
- Save and redeploy. The app **auto-creates** the `insightshop` database on first run (no manual `psql`).

---

## Option B: Manual setup (Console + CLI)

### Step 1: VPC and subnets

- Use a VPC that has **private subnets** (no direct internet; use NAT for outbound if needed).
- Note the **VPC ID** and **two private subnet IDs** (in different AZs for RDS).

### Step 2: DB subnet group

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name insightshop-db-subnets \
  --db-subnet-group-description "Subnets for InsightShop RDS" \
  --subnet-ids subnet-xxxx subnet-yyyy
```

### Step 3: Security groups

**RDS security group** – allow PostgreSQL from the VPC connector and from 18.193.0.149:

```bash
# Create SG for RDS
aws ec2 create-security-group \
  --group-name insightshop-rds-sg \
  --description "RDS PostgreSQL for InsightShop" \
  --vpc-id vpc-xxxxxxxxx

# Allow 5432 from the VPC CIDR (so App Runner via VPC connector can connect)
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-xxxxx \
  --protocol tcp --port 5432 --cidr 10.0.0.0/16

# Allow 18.193.0.149 (DBeaver)
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-xxxxx \
  --protocol tcp --port 5432 --cidr 18.193.0.149/32
```

**VPC connector security group** (optional; for connector itself):

```bash
aws ec2 create-security-group \
  --group-name insightshop-apprunner-connector-sg \
  --description "App Runner VPC connector" \
  --vpc-id vpc-xxxxxxxxx
# Egress is allowed by default; no need to allow 5432 out if you use RDS SG above.
```

### Step 4: Create RDS PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier insightshop-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15 \
  --master-username postgres \
  --master-user-password "YourSecurePassword123" \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-rds-xxxxx \
  --db-subnet-group-name insightshop-db-subnets \
  --no-publicly-accessible \
  --backup-retention-period 7
```

Wait until the instance is **available**:

```bash
aws rds wait db-instance-available --db-instance-identifier insightshop-db
```

Get the endpoint:

```bash
aws rds describe-db-instances \
  --db-instance-identifier insightshop-db \
  --query 'DBInstances[0].Endpoint.Address' --output text
```

**DATABASE_URL** (replace password and host):

```text
postgresql://postgres:YourSecurePassword123@insightshop-db.xxxxx.us-east-1.rds.amazonaws.com:5432/insightshop
```

The app **auto-creates** the `insightshop` database on first run if it doesn't exist (no manual `psql`).

### Step 5: Create App Runner VPC connector

Use **private subnets only** (same as RDS or same VPC):

```bash
aws apprunner create-vpc-connector \
  --vpc-connector-name insightshop-connector \
  --subnets subnet-xxxx subnet-yyyy \
  --security-groups sg-connector-xxxxx
```

Note the **VpcConnectorArn** from the output.

### Step 6: Configure App Runner service

1. **Add DATABASE_URL**
   - **App Runner** → your service → **Configuration** → **Edit**.
   - Under **Environment variables**, add:
     - Key: `DATABASE_URL`
     - Value: `postgresql://postgres:YourSecurePassword123@insightshop-db.xxxxx.us-east-1.rds.amazonaws.com:5432/insightshop`
   - Prefer storing the value in **Secrets Manager** and adding it as a **Runtime environment secret** (variable name `DATABASE_URL`, secret ARN).

2. **Attach VPC connector**
   - In the same **Configuration** → **Networking** (or **Edit**):
   - Set **Outgoing traffic** → **VPC connector** to `insightshop-connector` (or the ARN from step 5).

3. **Save** and trigger a new deployment so the app picks up `DATABASE_URL` and uses the connector.

---

## Optional: DATABASE_URL in GitHub Actions

To inject `DATABASE_URL` when the workflow **creates** the App Runner service (e.g. first deploy), add a GitHub secret:

- **Name**: `DATABASE_URL`
- **Value**: `postgresql://postgres:PASSWORD@your-rds-endpoint:5432/insightshop`

Then ensure the workflow passes it into `RuntimeEnvironmentVariables` when the service is created. The [deploy-apprunner](deploy-apprunner.md) workflow can be extended to include `DATABASE_URL` from secrets if present; for existing services, update **Configuration** in the Console and redeploy.

---

## First run with PostgreSQL

On first start with `DATABASE_URL` set, the app will:

- **Create the database** if it doesn't exist (connects to `postgres`, then `CREATE DATABASE`).
- Create tables (`db.create_all()`).
- Run any column backfills (e.g. `orders.currency`, `products.season`) if the schema expects them.

No manual `psql` or migration step is required unless you use Flask-Migrate.

---

## Restrict DB access to 18.193.0.149

To allow **only** 18.193.0.149 (and App Runner via the VPC connector) to connect to the database, use a single RDS security group with two ingress rules:

- Port 5432 from **18.193.0.149/32** (DBeaver).
- Port 5432 from the **VPC CIDR** or the **VPC connector security group** (App Runner).

See [DATABASE_IP_RESTRICTION.md](DATABASE_IP_RESTRICTION.md) and the script `scripts/aws_db_security_group_allow_ip.py` for the DBeaver-only SG; combine with the app rule as above.

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| App can't connect to RDS | VPC connector attached? Subnets are **private**? RDS SG allows 5432 from connector/VPC CIDR? |
| Health check fails after adding DB | App may need more startup time; check logs. Ensure `DATABASE_URL` is correct and RDS is **available**. |
| DBeaver can't connect | RDS SG allows **18.193.0.149/32** on 5432; RDS is in a subnet reachable from the internet or via VPN/bastion. If RDS is private-only, use a bastion or connect from a resource in the VPC. |

For App Runner VPC outbound failures, see [AWS docs](https://docs.aws.amazon.com/apprunner/latest/dg/troubleshooting.vpc-outbound-connect-failure.html).
