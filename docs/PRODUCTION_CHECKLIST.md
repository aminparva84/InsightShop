# Production Deployment Checklist

## 🎯 Quick Decision Guide

### Question: Should I use separate containers for DB?

**Answer: NO - Use Managed RDS instead**

- ❌ **Don't**: Put database in a container (data loss, no backups, scaling issues)
- ✅ **Do**: Use AWS RDS PostgreSQL/MySQL (managed, backups, high availability)

### Question: All-in-one container or separate services?

**Answer: Hybrid Approach**

- ✅ **Application Container**: Flask + React build (single container is fine)
- ✅ **Database**: Separate RDS instance (managed service)
- ✅ **Vector DB**: EFS mount or separate managed service
- ✅ **AI Service**: AWS Bedrock (external service)

---

## 🚀 Recommended Architecture for Production

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFront CDN                            │
│              (Static assets, caching)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Application Load Balancer                       │
│              (HTTPS, SSL Termination)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  ECS Fargate     │    │  ECS Fargate     │
│  (Auto-scaling)  │    │  (Auto-scaling)  │
│                  │    │                  │
│  Container:      │    │  Container:      │
│  • Flask App     │    │  • Flask App     │
│  • React Build   │    │  • React Build   │
│  • ChromaDB      │    │  • ChromaDB      │
│    (EFS mount)   │    │    (EFS mount)   │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  RDS PostgreSQL  │    │  ElastiCache    │
│  (Multi-AZ)      │    │  (Redis)         │
│  • Auto backups │    │  • Session store│
│  • High avail.  │    │  • Caching       │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  • AWS Bedrock (Claude AI)                                   │
│  • AWS Secrets Manager (credentials)                         │
│  • S3 (backups, static assets)                              │
│  • CloudWatch (monitoring, logs)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Pre-Deployment Checklist

### Code Quality
- [ ] Remove all `print()` statements, use proper logging
- [ ] Remove debug code and test endpoints
- [ ] Set `DEBUG=False` in production
- [ ] Review and fix all TODO/FIXME comments
- [ ] Run linters and fix all warnings
- [ ] Code review completed

### Security
- [ ] CORS configured for specific domains (not `*`)
- [ ] JWT_SECRET is 32+ characters, stored in Secrets Manager
- [ ] AWS credentials in Secrets Manager (not env vars)
- [ ] Database passwords in Secrets Manager
- [ ] HTTPS enforced (App Runner/ALB handles this)
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (using SQLAlchemy ORM)
- [ ] XSS protection (React handles this)

### Database
- [ ] Migrated from SQLite to PostgreSQL/RDS
- [ ] Database migrations scripted
- [ ] Connection pooling configured
- [ ] Backup strategy implemented
- [ ] Restore procedure tested
- [ ] Database indexes optimized

### Configuration
- [ ] All secrets in AWS Secrets Manager
- [ ] Environment variables documented
- [ ] Config values validated on startup
- [ ] Feature flags for gradual rollout

### Monitoring & Logging
- [ ] CloudWatch Logs configured
- [ ] Error tracking (CloudWatch or Sentry)
- [ ] Health check endpoint (`/api/health`)
- [ ] Metrics dashboard created
- [ ] Alarms configured (errors, latency, CPU)
- [ ] Log retention policy set

### Performance
- [ ] Database queries optimized
- [ ] Caching strategy implemented (ElastiCache)
- [ ] CDN configured for static assets
- [ ] Image optimization
- [ ] API response times acceptable (<200ms)
- [ ] Load testing completed

### Backup & Recovery
- [ ] Automated database backups (RDS)
- [ ] S3 backup strategy for ChromaDB
- [ ] Restore procedure documented
- [ ] Disaster recovery plan
- [ ] Backup restoration tested

### CI/CD
- [ ] Docker image builds successfully
- [ ] Automated tests pass
- [ ] Deployment pipeline configured
- [ ] Rollback procedure tested
- [ ] Blue-green deployment ready

---

## 🔧 Required Code Changes for Production

### 1. Update CORS Configuration

```python
# app.py
CORS(app, resources={
    r"/api/*": {
        "origins": [
            os.getenv('FRONTEND_URL', 'https://yourdomain.com'),
            os.getenv('FRONTEND_URL_WWW', 'https://www.yourdomain.com')
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
```

### 2. Add Proper Logging

```python
# app.py
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/insightshop.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('InsightShop startup')
```

### 3. Add Database Connection Pooling

```python
# config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20
}
```

### 4. Add Rate Limiting

```python
# Install: pip install flask-limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to endpoints
@ai_agent_bp.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    # ...
```

---

## 📊 Cost Estimation (Monthly)

### Option 1: App Runner (MVP)
- App Runner: $30-60
- S3 (backups): $1-5
- CloudWatch: $5-10
- **Total: ~$40-75/month**

### Option 2: ECS Fargate + RDS (Production)
- ECS Fargate (2 tasks): $40-80
- RDS PostgreSQL (db.t3.small): $30-50
- ALB: $16
- EFS: $3-10
- CloudWatch: $10-20
- **Total: ~$100-180/month**

### Option 3: EC2 + RDS (Cost-Optimized)
- EC2 (t3.medium): $30
- RDS (db.t3.micro): $15
- ALB: $16
- **Total: ~$60-100/month**

---

## 🎯 My Final Recommendation

### For Your Situation:

**Start with: App Runner + S3 Backups**
- Fastest to deploy
- Good enough for initial launch
- Can migrate later without downtime

**Migrate to: ECS Fargate + RDS (when you hit 10k+ users/month)**
- Production-grade
- Better performance
- Proper database management

**Why NOT all-in-one container?**
- ❌ Database in container = data loss on restart
- ❌ No automated backups
- ❌ Can't scale database independently
- ❌ No high availability

**Why separate RDS?**
- ✅ Managed service (backups, patches, monitoring)
- ✅ High availability (Multi-AZ)
- ✅ Auto-scaling
- ✅ Point-in-time recovery
- ✅ Security best practices

---

## 🚀 Quick Start Commands

### Deploy to App Runner (Now)

```bash
# 1. Build and push to ECR
docker build -t insightshop:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag insightshop:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest

# 2. Create App Runner service (via Console or CLI)
# See AWS_DEPLOYMENT_GUIDE.md for details
```

### Migrate to ECS Fargate (Later)

```bash
# 1. Create RDS instance
aws rds create-db-instance --db-instance-identifier insightshop-db --engine postgresql ...

# 2. Migrate data
python scripts/migrate_to_postgresql.py

# 3. Create ECS cluster and service
# See AWS_DEPLOYMENT_GUIDE.md for details
```

---

## 📞 Need Help?

- Review `AWS_DEPLOYMENT_GUIDE.md` for detailed steps
- Check `ARCHITECTURE.md` for system design
- AWS Documentation: https://docs.aws.amazon.com/

