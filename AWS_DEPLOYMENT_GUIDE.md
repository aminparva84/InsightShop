# AWS Deployment Guide & Architecture Review

## 🏗️ Architecture Review & Best Practices

### ✅ Current Architecture Strengths

1. **Layered Architecture**: Clean separation between presentation, API, processing, and data layers
2. **Modular Design**: Blueprint-based routing, separate utilities
3. **Vector Search**: ChromaDB for semantic search is a good choice
4. **AI Integration**: Well-structured Bedrock integration with fallbacks
5. **Multi-stage Docker Build**: Efficient containerization

### ⚠️ Areas for Improvement (Production Readiness)

1. **Database**: SQLite is NOT production-ready for containers
   - ❌ No concurrent writes support
   - ❌ Data loss on container restart/redeploy
   - ❌ No backup/recovery built-in
   - ✅ **Recommendation**: Migrate to RDS PostgreSQL/MySQL

2. **Vector Database**: ChromaDB file-based storage
   - ⚠️ Data loss on container restart
   - ✅ **Recommendation**: Use EFS mount or migrate to managed vector DB

3. **Secrets Management**: Environment variables in plain text
   - ⚠️ Security risk
   - ✅ **Recommendation**: Use AWS Secrets Manager

4. **CORS Configuration**: Currently allows all origins (`"origins": "*"`)
   - ⚠️ Security risk in production
   - ✅ **Recommendation**: Restrict to specific domains

5. **Database Connection Pooling**: Not configured
   - ✅ **Recommendation**: Add connection pooling for RDS

---

## 🚀 AWS Deployment Options

### Option 1: AWS App Runner (Recommended for Start)

**Architecture:**
```
┌─────────────────────────────────────────┐
│         AWS App Runner                  │
│  ┌───────────────────────────────────┐ │
│  │  Single Container                 │ │
│  │  • Flask App                       │ │
│  │  • React Build (static)            │ │
│  │  • SQLite DB (⚠️ ephemeral)        │ │
│  │  • ChromaDB (⚠️ ephemeral)       │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  EFS Mount (optional)              │ │
│  │  • Persistent storage for DB       │ │
│  │  • Persistent storage for vectors  │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
         │
         ▼
    AWS Bedrock (Claude)
```

**Pros:**
- ✅ Simple deployment (just push Docker image)
- ✅ Auto-scaling built-in
- ✅ No infrastructure management
- ✅ Pay per use
- ✅ HTTPS/SSL included
- ✅ Good for MVP/early stage

**Cons:**
- ⚠️ SQLite in container = data loss on redeploy
- ⚠️ Limited customization
- ⚠️ EFS mounting requires custom setup
- ⚠️ Not ideal for high-traffic production

**Cost:** ~$0.007/vCPU-hour + $0.0008/GB-hour (~$30-100/month for small-medium traffic)

**Best For:** MVP, small-medium traffic, quick deployment

---

### Option 2: ECS Fargate + RDS (Recommended for Production)

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    Application Load Balancer             │
│                    (HTTPS, SSL Termination)             │
└────────────────────┬──────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  ECS Fargate     │    │  ECS Fargate     │
│  (App Container) │    │  (App Container) │
│                  │    │                  │
│  • Flask App     │    │  • Flask App     │
│  • React Build   │    │  • React Build   │
│  • ChromaDB      │    │  • ChromaDB      │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   RDS PostgreSQL │    │   EFS (optional)  │
│   (Primary DB)   │    │   (ChromaDB)     │
└─────────────────┘    └─────────────────┘
         │
         ▼
    AWS Bedrock
```

**Pros:**
- ✅ Production-ready database (RDS)
- ✅ Auto-scaling containers
- ✅ High availability
- ✅ Automated backups
- ✅ Multi-AZ support
- ✅ Connection pooling
- ✅ Better performance

**Cons:**
- ⚠️ More complex setup
- ⚠️ Higher cost (~$50-200/month)
- ⚠️ Need to manage RDS

**Cost:** 
- ECS Fargate: ~$0.04/vCPU-hour + $0.004/GB-hour
- RDS PostgreSQL (db.t3.micro): ~$15/month
- ALB: ~$16/month
- **Total: ~$80-150/month**

**Best For:** Production, medium-high traffic, need reliability

---

### Option 3: EC2 + RDS (Traditional, More Control)

**Architecture:**
```
┌─────────────────────────────────────────┐
│         Application Load Balancer       │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   EC2 Instance   │    │   EC2 Instance   │
│   (Auto Scaling) │    │   (Auto Scaling) │
│                  │    │                  │
│  Docker Compose:│    │  Docker Compose: │
│  • Flask App     │    │  • Flask App     │
│  • ChromaDB     │    │  • ChromaDB      │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   RDS PostgreSQL │    │   ElastiCache    │
│   (Primary DB)   │    │   (Redis Cache)  │
└─────────────────┘    └─────────────────┘
```

**Pros:**
- ✅ Full control over infrastructure
- ✅ Can optimize for specific needs
- ✅ Can use reserved instances (cost savings)
- ✅ Good for predictable workloads

**Cons:**
- ⚠️ Need to manage EC2 instances
- ⚠️ Need to handle scaling manually
- ⚠️ More operational overhead
- ⚠️ Need to handle security patches

**Cost:** 
- EC2 (t3.medium): ~$30/month
- RDS: ~$15/month
- **Total: ~$60-100/month** (can be cheaper with reserved instances)

**Best For:** Predictable traffic, need full control, cost optimization

---

### Option 4: Elastic Beanstalk (Simplified ECS)

**Architecture:** Similar to ECS but managed by Elastic Beanstalk

**Pros:**
- ✅ Easier than raw ECS
- ✅ Auto-scaling built-in
- ✅ Environment management
- ✅ Can use RDS easily

**Cons:**
- ⚠️ Less flexible than ECS
- ⚠️ Platform-specific

**Best For:** Quick deployment with some control

---

## 🎯 My Recommendation: Hybrid Approach

### Phase 1: MVP/Launch (App Runner + EFS)
**Use App Runner with EFS for persistence**

**Why:**
- Fastest to deploy
- Low operational overhead
- Good enough for initial launch
- Can migrate later

**Setup:**
1. Deploy to App Runner
2. Mount EFS for `/app/data` (SQLite) and `/app/vector_db` (ChromaDB)
3. Set up automated backups to S3

**Cost:** ~$40-80/month

---

### Phase 2: Production (ECS Fargate + RDS)
**Migrate to ECS Fargate with RDS PostgreSQL**

**Why:**
- Production-grade database
- Better performance
- High availability
- Scalability

**Migration Steps:**
1. Set up RDS PostgreSQL
2. Migrate SQLite data to PostgreSQL
3. Update connection strings
4. Deploy to ECS Fargate
5. Use EFS for ChromaDB (or migrate to managed vector DB)

**Cost:** ~$100-200/month

---

## 📋 Detailed Deployment Plan

### Option A: App Runner with EFS (Quick Start)

#### Step 1: Create EFS File System

```bash
# Create EFS
aws efs create-file-system \
  --creation-token insightshop-efs \
  --performance-mode generalPurpose \
  --throughput-mode provisioned \
  --provisioned-throughput-in-mibps 100 \
  --encrypted

# Note the FileSystemId
EFS_ID="fs-xxxxxxxxx"

# Create mount targets in your VPC subnets
aws efs create-mount-target \
  --file-system-id $EFS_ID \
  --subnet-id subnet-xxxxx \
  --security-groups sg-xxxxx
```

#### Step 2: Update Dockerfile for EFS

```dockerfile
# Add EFS mount point
VOLUME ["/app/data", "/app/vector_db"]
```

#### Step 3: Update App Runner Configuration

**Note:** App Runner doesn't natively support EFS. You'll need to:
- Use a sidecar container pattern, OR
- Use S3 for backups and restore on startup, OR
- Migrate to ECS Fargate (recommended)

#### Step 4: Implement S3 Backup Strategy

```python
# scripts/backup_to_s3.py
import boto3
from datetime import datetime
from config import Config
import os

def backup_database():
    s3 = boto3.client('s3')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Backup SQLite
    db_path = Config.DB_PATH
    if os.path.exists(db_path):
        s3.upload_file(
            db_path,
            'your-backup-bucket',
            f'database/insightshop_{timestamp}.db'
        )
    
    # Backup ChromaDB (as tar)
    import tarfile
    vector_db_path = Config.VECTOR_DB_PATH
    if os.path.exists(vector_db_path):
        with tarfile.open(f'/tmp/vector_db_{timestamp}.tar.gz', 'w:gz') as tar:
            tar.add(vector_db_path, arcname='vector_db')
        s3.upload_file(
            f'/tmp/vector_db_{timestamp}.tar.gz',
            'your-backup-bucket',
            f'vector_db/vector_db_{timestamp}.tar.gz'
        )
```

---

### Option B: ECS Fargate + RDS (Production)

#### Step 1: Create RDS PostgreSQL Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier insightshop-db \
  --db-instance-class db.t3.micro \
  --engine postgresql \
  --master-username admin \
  --master-user-password YourSecurePassword \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --multi-az
```

#### Step 2: Update Database Configuration

```python
# config.py - Add PostgreSQL support
import os
from urllib.parse import quote_plus

class Config:
    # Database Configuration
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'
    
    if DB_TYPE == 'postgresql':
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '5432')
        DB_NAME = os.getenv('DB_NAME', 'insightshop')
        DB_USER = os.getenv('DB_USER', 'admin')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        # SQLite (development)
        DB_PATH = os.getenv('DB_PATH', 'insightshop.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
```

#### Step 3: Create ECS Task Definition

```json
{
  "family": "insightshop",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "insightshop-app",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"},
        {"name": "DB_TYPE", "value": "postgresql"},
        {"name": "DB_HOST", "value": "insightshop-db.xxxxx.us-east-1.rds.amazonaws.com"}
      ],
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxxxx:secret:insightshop/db-password"
        },
        {
          "name": "JWT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxxxx:secret:insightshop/jwt-secret"
        }
      ],
      "mountPoints": [
        {
          "sourceVolume": "vector-db",
          "containerPath": "/app/vector_db"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/insightshop",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "volumes": [
    {
      "name": "vector-db",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxxxxxx",
        "rootDirectory": "/vector_db",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

#### Step 4: Create ECS Service

```bash
aws ecs create-service \
  --cluster insightshop-cluster \
  --service-name insightshop-service \
  --task-definition insightshop \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:xxxxx:targetgroup/insightshop-tg/xxxxx,containerName=insightshop-app,containerPort=5000"
```

---

## 🔐 Security Best Practices

### 1. Use AWS Secrets Manager

```python
# utils/secrets.py
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage in config.py
try:
    secrets = get_secret('insightshop/secrets')
    Config.DB_PASSWORD = secrets['db_password']
    Config.JWT_SECRET = secrets['jwt_secret']
    Config.AWS_SECRET_ACCESS_KEY = secrets['aws_secret_key']
except:
    # Fallback to environment variables
    pass
```

### 2. Restrict CORS

```python
# app.py
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://yourdomain.com",
            "https://www.yourdomain.com"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 3. Use IAM Roles (Not Access Keys)

```python
# Use IAM role for Bedrock access
# Remove AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from config
# App Runner/ECS will use IAM role automatically
```

### 4. Enable Database Encryption

- RDS: Enable encryption at rest
- EFS: Enable encryption in transit and at rest
- S3: Enable bucket encryption

---

## 📊 Cost Comparison

| Option | Monthly Cost | Best For |
|-------|-------------|----------|
| App Runner (no persistence) | $30-60 | Development/Testing |
| App Runner + EFS | $50-100 | MVP/Small Production |
| ECS Fargate + RDS | $100-200 | Production |
| EC2 + RDS | $60-150 | Cost-optimized Production |

---

## 🎯 Final Recommendation

### For Launch (Now):
**Use App Runner with S3 backups** (quickest path)

1. Deploy to App Runner
2. Implement S3 backup script (runs on schedule)
3. Restore from S3 on container startup if DB missing
4. Monitor and iterate

### For Production (3-6 months):
**Migrate to ECS Fargate + RDS PostgreSQL**

1. Set up RDS PostgreSQL
2. Migrate data from SQLite
3. Deploy to ECS Fargate
4. Use EFS for ChromaDB persistence
5. Set up auto-scaling
6. Configure CloudWatch monitoring

### Why This Approach?
- ✅ Start simple, scale as needed
- ✅ No over-engineering
- ✅ Can migrate without downtime
- ✅ Cost-effective progression
- ✅ Production-ready when needed

---

## 📝 Migration Checklist

### SQLite → PostgreSQL Migration

1. **Install PostgreSQL adapter**
   ```bash
   pip install psycopg2-binary
   ```

2. **Create migration script**
   ```python
   # scripts/migrate_to_postgresql.py
   from sqlalchemy import create_engine
   import pandas as pd
   
   # Connect to both databases
   sqlite_engine = create_engine('sqlite:///insightshop.db')
   postgres_engine = create_engine('postgresql://user:pass@host/db')
   
   # Migrate each table
   tables = ['users', 'products', 'cart_items', 'orders', 'order_items', 'payments']
   for table in tables:
       df = pd.read_sql_table(table, sqlite_engine)
       df.to_sql(table, postgres_engine, if_exists='append', index=False)
   ```

3. **Update connection strings**
4. **Test thoroughly**
5. **Deploy with feature flag**
6. **Monitor and verify**

---

## 🚨 Critical Production Considerations

1. **Database Backups**: Automated daily backups
2. **Monitoring**: CloudWatch alarms for errors, latency
3. **Logging**: Centralized logging (CloudWatch Logs)
4. **Health Checks**: `/api/health` endpoint
5. **Auto-scaling**: Configure based on CPU/memory
6. **CDN**: Use CloudFront for static assets
7. **SSL/TLS**: Always use HTTPS
8. **Rate Limiting**: Implement API rate limits
9. **Error Handling**: Proper error responses
10. **Database Connection Pooling**: Configure SQLAlchemy pool

---

## 📚 Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [ECS Fargate Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [RDS PostgreSQL Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.PostgreSQL.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

