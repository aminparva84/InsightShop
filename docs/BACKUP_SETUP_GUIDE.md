# S3 Backup Setup Guide

## 🎯 Quick Setup

### Step 1: Create S3 Bucket

```bash
# Run the setup script
python scripts/setup_s3_backup_bucket.py insightshop-backups us-east-1
```

Or manually:
```bash
aws s3 mb s3://insightshop-backups --region us-east-1
```

### Step 2: Set Environment Variable

Add to your `.env` file:
```env
S3_BACKUP_BUCKET=insightshop-backups
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

### Step 3: Test Backup

```bash
python scripts/backup_to_s3.py
```

### Step 4: Schedule Automated Backups

#### Option A: Cron Job (Linux/Mac)
```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/InsightShop && python scripts/backup_to_s3.py >> /var/log/insightshop_backup.log 2>&1
```

#### Option B: Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\InsightShop\scripts\backup_to_s3.py`

#### Option C: AWS EventBridge (Recommended for Production)
```json
{
  "Rules": [
    {
      "Name": "insightshop-daily-backup",
      "ScheduleExpression": "cron(0 2 * * ? *)",
      "State": "ENABLED",
      "Targets": [
        {
          "Arn": "arn:aws:lambda:us-east-1:ACCOUNT:function:backup-function",
          "Id": "1"
        }
      ]
    }
  ]
}
```

## 📋 Backup Scripts

### Backup Scripts Created:
1. **`scripts/backup_to_s3.py`** - Automated backup
2. **`scripts/restore_from_s3.py`** - Restore from backup
3. **`scripts/setup_s3_backup_bucket.py`** - Setup S3 bucket

## 🔄 Restore from Backup

### PostgreSQL (when `DATABASE_URL` is set)

- **From a local dump file** (e.g. a `.sql` you have from a previous `pg_dump` or from S3 download):
  ```bash
  cd C:\code\InsightShop
  set PYTHONPATH=%CD%
  python scripts/restore_from_s3.py path\to\backup.sql
  ```
- **From S3** (after you have run `backup_to_s3.py` at least once):
  ```bash
  set PYTHONPATH=%CD%
  python scripts/restore_from_s3.py list
  python scripts/restore_from_s3.py latest --yes
  ```

### SQLite (when `DATABASE_URL` is not set)

- **List backups:** `python scripts/restore_from_s3.py list`
- **Restore latest:** `python scripts/restore_from_s3.py latest` (add `--yes` to skip prompt)
- **Restore by timestamp:** `python scripts/restore_from_s3.py 20241201_020000`

## 💰 S3 Backup Costs

**Storage Costs:**
- First 50 TB: $0.023/GB-month (Standard)
- After 90 days: $0.004/GB-month (Glacier) - automatic via lifecycle policy

**Example:**
- 10 GB database backups
- 30-day retention
- **Cost: ~$0.23/month**

Very affordable!

## ✅ Backup Features

- ✅ Automated daily/hourly backups
- ✅ Encrypted (AES256)
- ✅ Versioned (can restore any version)
- ✅ Lifecycle management (moves to Glacier after 90 days)
- ✅ Automatic cleanup (deletes after 1 year)
- ✅ Multi-tenant support (separate folders per instance)

