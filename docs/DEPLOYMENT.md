# Deployment Guide for AWS App Runner

This guide walks you through deploying InsightShop to AWS App Runner.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. Docker installed locally
4. ECR repository created

## Step 1: Prepare Environment Variables

Create a `.env` file or prepare environment variables for App Runner:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
JWT_SECRET=your-32-character-secret-key
FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
BASE_URL=https://your-app-runner-url.us-east-1.awsapprunner.com
WORKMAIL_SMTP_SERVER=smtp.mail.us-east-1.awsapps.com
WORKMAIL_SMTP_PORT=465
WORKMAIL_SMTP_USERNAME=your_username
WORKMAIL_SMTP_PASSWORD=your_password
USE_WORKMAIL=true
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FLASK_ENV=production
DEBUG=False
```

## Step 2: Build and Push Docker Image

```bash
# Build the image
docker build -t insightshop:latest .

# Create ECR repository (if not exists)
aws ecr create-repository --repository-name insightshop --region us-east-1

# Get ECR login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag the image
docker tag insightshop:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest
```

## Step 3: Create App Runner Service

### Option A: Using AWS Console

1. Go to AWS App Runner console
2. Click "Create service"
3. Choose "Container registry" → "Amazon ECR"
4. Select your ECR repository and image
5. Configure:
   - Service name: `insightshop`
   - Port: `5000`
   - Environment variables: Add all from your `.env` file
6. Configure auto-deployment
7. Review and create

### Option B: Using AWS CLI

```bash
aws apprunner create-service \
  --service-name insightshop \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest",
      "ImageConfiguration": {
        "Port": "5000",
        "RuntimeEnvironmentVariables": {
          "FLASK_ENV": "production",
          "PYTHONUNBUFFERED": "1"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --auto-scaling-configuration-arn <your-auto-scaling-config-arn>
```

## Step 4: Configure Environment Variables

After service creation, add all environment variables:

1. Go to App Runner service → Configuration → Environment variables
2. Add each variable from your `.env` file
3. Save and deploy

## Step 5: Configure Auto-Deployment (Optional)

1. Enable auto-deployment in App Runner settings
2. Set up GitHub Actions or CI/CD pipeline to:
   - Build Docker image on push
   - Push to ECR
   - App Runner will auto-deploy

## Step 6: Database Persistence

**Important**: SQLite databases in containers are ephemeral. For production:

1. **Option 1**: Use EFS (Elastic File System) mounted to `/app/data`
2. **Option 2**: Migrate to RDS (PostgreSQL/MySQL)
3. **Option 3**: Use S3 for database backups

### Using EFS:

1. Create EFS file system
2. Mount in App Runner (requires custom configuration)
3. Update `DB_PATH` to use EFS mount point

### Using S3 Backup:

Create a cron job or scheduled task to backup database to S3:

```python
# scripts/backup_db.py
import boto3
from datetime import datetime
from config import Config

s3 = boto3.client('s3')
backup_key = f"backups/db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
s3.upload_file(Config.DB_PATH, 'your-bucket', backup_key)
```

## Step 7: Vector Database Persistence

Similar to database, ChromaDB data should be persisted:

1. Use EFS for `/app/vector_db`
2. Or configure ChromaDB to use S3 backend

## Step 8: Health Checks

App Runner automatically uses `/api/health` endpoint for health checks.

## Step 9: Custom Domain (Optional)

1. Go to App Runner service → Custom domains
2. Add your domain
3. Configure DNS records as instructed

## Step 10: Monitoring

1. Set up CloudWatch alarms
2. Monitor logs in App Runner console
3. Set up error notifications

## Troubleshooting

### Service won't start
- Check logs in App Runner console
- Verify environment variables
- Check database initialization

### Database not persisting
- Use EFS or migrate to RDS
- Implement S3 backup strategy

### AI Agent not working
- Verify Bedrock permissions
- Check AWS credentials
- Verify model ID is correct

### Email not sending
- Verify WorkMail/SES configuration
- Check email verification status
- Review SMTP credentials

## Cost Optimization

1. Use appropriate instance sizes
2. Configure auto-scaling
3. Use CloudFront for static assets
4. Implement caching strategies
5. Monitor and optimize database queries

## Security Best Practices

1. Use AWS Secrets Manager for sensitive data
2. Enable HTTPS only
3. Configure CORS properly
4. Use IAM roles instead of access keys when possible
5. Regular security updates
6. Enable CloudWatch logging
7. Set up WAF if needed

