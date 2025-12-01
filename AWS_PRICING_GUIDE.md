# AWS Deployment Pricing Guide - InsightShop

## 💰 Detailed Cost Breakdown by Deployment Option

### Option 1: AWS App Runner (Simplest)

#### Monthly Cost Breakdown

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| **App Runner** | 1 vCPU, 2 GB RAM | $0.007/vCPU-hour × 730 hours = **$5.11** |
| | 2 GB RAM | $0.0008/GB-hour × 730 hours × 2 GB = **$1.17** |
| **Data Transfer** | First 100 GB free, then $0.09/GB | **$0-10** (depends on traffic) |
| **S3 (Backups)** | 10 GB storage, minimal requests | **$0.25** |
| **CloudWatch Logs** | 5 GB ingestion, 30-day retention | **$2.50** |
| **CloudWatch Metrics** | Standard metrics | **$0** (free tier) |
| **Total (Low Traffic)** | | **~$9-20/month** |
| **Total (Medium Traffic)** | 500 GB transfer | **~$50-70/month** |

#### Cost Details:
- **vCPU Hours**: $0.007 per vCPU-hour (24/7 = 730 hours/month)
- **Memory**: $0.0008 per GB-hour
- **Auto-scaling**: Only pay for what you use
- **No idle costs**: Scales to zero when not in use (if configured)

#### Example Scenarios:

**Scenario 1: Development/Testing (Low Traffic)**
- 1 vCPU, 2 GB RAM, minimal traffic
- **Cost: ~$9-15/month**

**Scenario 2: Small Production (100-1000 users/day)**
- 1-2 vCPU, 2-4 GB RAM, moderate traffic
- **Cost: ~$20-50/month**

**Scenario 3: Medium Production (1000-10000 users/day)**
- 2-4 vCPU, 4-8 GB RAM, high traffic
- **Cost: ~$50-150/month**

#### Pros:
- ✅ No infrastructure management
- ✅ Pay only for what you use
- ✅ Auto-scaling included
- ✅ HTTPS/SSL included

#### Cons:
- ⚠️ Can get expensive at scale
- ⚠️ Limited customization
- ⚠️ SQLite persistence issues (need EFS workaround)

---

### Option 2: ECS Fargate + RDS (Production Recommended)

#### Monthly Cost Breakdown

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| **ECS Fargate** | 2 tasks, 0.5 vCPU, 1 GB each | $0.04/vCPU-hour × 730 × 1 vCPU = **$29.20** |
| | 1 GB RAM × 2 tasks | $0.004/GB-hour × 730 × 2 GB = **$5.84** |
| **Application Load Balancer** | Standard ALB | **$16.20** (fixed) |
| **ALB Data Processing** | LCU hours | **$0.008/LCU-hour × 730 = $5.84** |
| **RDS PostgreSQL** | db.t3.micro (1 vCPU, 1 GB) | **$15.00** |
| **RDS Storage** | 20 GB gp3 | **$2.30** |
| **RDS Backup Storage** | 7 days retention, 20 GB | **$2.30** |
| **EFS (ChromaDB)** | 10 GB standard storage | **$3.00** |
| **EFS Requests** | Minimal | **$0.10** |
| **S3 (Backups)** | 10 GB | **$0.25** |
| **CloudWatch Logs** | 10 GB ingestion | **$5.00** |
| **Data Transfer Out** | First 100 GB free | **$0-10** |
| **Total (Minimum)** | | **~$82-95/month** |
| **Total (With Traffic)** | 500 GB transfer | **~$100-120/month** |

#### Cost Details:

**ECS Fargate:**
- vCPU: $0.04 per vCPU-hour
- Memory: $0.004 per GB-hour
- Example: 2 tasks × 0.5 vCPU × 1 GB = $29.20 + $5.84 = **$35.04/month**

**RDS PostgreSQL:**
- db.t3.micro: $15/month (1 vCPU, 1 GB RAM)
- db.t3.small: $30/month (2 vCPU, 2 GB RAM) - recommended for production
- Storage: $0.115/GB-month (gp3)
- Backup: $0.095/GB-month (first backup free)

**Application Load Balancer:**
- Fixed: $0.0225/hour = **$16.20/month**
- LCU: $0.008/LCU-hour (varies by traffic)

#### Example Scenarios:

**Scenario 1: Small Production (2 tasks, db.t3.micro)**
- **Cost: ~$85-100/month**

**Scenario 2: Medium Production (4 tasks, db.t3.small)**
- ECS: 4 tasks × 1 vCPU × 2 GB = $116.80 + $23.36 = **$140.16**
- RDS: db.t3.small = **$30**
- ALB: **$22**
- **Total: ~$200-220/month**

**Scenario 3: High Traffic (8 tasks, db.t3.medium)**
- ECS: 8 tasks × 2 vCPU × 4 GB = $467.20 + $93.44 = **$560.64**
- RDS: db.t3.medium = **$60**
- ALB: **$30**
- **Total: ~$650-700/month**

#### Pros:
- ✅ Production-grade database
- ✅ High availability
- ✅ Better performance
- ✅ Proper scaling

#### Cons:
- ⚠️ Higher base cost (~$80/month minimum)
- ⚠️ More complex setup
- ⚠️ Need to manage RDS

---

### Option 3: EC2 + RDS (Cost-Optimized)

#### Monthly Cost Breakdown

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| **EC2 Instance** | t3.medium (2 vCPU, 4 GB) | **$30.00** (on-demand) |
| **EC2 Instance** | t3.medium (reserved 1-year) | **$18.00** (savings: 40%) |
| **EBS Storage** | 30 GB gp3 | **$3.00** |
| **Application Load Balancer** | Standard ALB | **$16.20** |
| **ALB Data Processing** | LCU hours | **$5.84** |
| **RDS PostgreSQL** | db.t3.micro | **$15.00** |
| **RDS Storage** | 20 GB | **$2.30** |
| **RDS Backup** | 7 days | **$2.30** |
| **EFS (ChromaDB)** | 10 GB | **$3.00** |
| **CloudWatch** | Logs + metrics | **$5.00** |
| **Data Transfer** | First 100 GB free | **$0-10** |
| **Total (On-Demand)** | | **~$82-95/month** |
| **Total (Reserved 1-year)** | | **~$70-85/month** |
| **Total (Reserved 3-year)** | 60% savings | **~$55-70/month** |

#### Cost Details:

**EC2 t3.medium:**
- On-demand: $0.0416/hour = **$30/month**
- Reserved 1-year (no upfront): $0.025/hour = **$18/month** (40% savings)
- Reserved 3-year (no upfront): $0.0167/hour = **$12/month** (60% savings)

**Alternative Instances:**
- t3.small: $15/month (on-demand) - might be enough
- t3.large: $60/month (on-demand) - for higher traffic

#### Example Scenarios:

**Scenario 1: Single EC2 (t3.medium on-demand)**
- **Cost: ~$85-100/month**

**Scenario 2: Single EC2 (t3.medium reserved 1-year)**
- **Cost: ~$70-85/month** (saves $15/month)

**Scenario 3: Auto-scaling Group (2-4 instances)**
- Base: 2 × t3.medium = $60/month
- Peak: +2 instances = +$30/month
- **Cost: ~$90-150/month** (varies by traffic)

#### Pros:
- ✅ Can be cheaper with reserved instances
- ✅ Full control
- ✅ Predictable costs
- ✅ Can optimize for specific needs

#### Cons:
- ⚠️ Need to manage EC2
- ⚠️ Manual scaling (or setup auto-scaling)
- ⚠️ More operational overhead
- ⚠️ Need to handle patches/updates

---

### Option 4: Elastic Beanstalk (Simplified ECS)

#### Monthly Cost Breakdown

Similar to ECS Fargate, but with additional management layer:
- **Base Cost**: Same as ECS Fargate (~$80-100/month)
- **No additional charges** for Beanstalk itself
- **Pros**: Easier management, same cost
- **Cons**: Less flexibility than raw ECS

---

## 📊 Cost Comparison Table

| Deployment Option | Monthly Cost (Low) | Monthly Cost (Medium) | Monthly Cost (High) | Best For |
|------------------|-------------------|----------------------|---------------------|----------|
| **App Runner** | $9-20 | $50-70 | $150-300 | MVP, Quick Launch |
| **ECS Fargate + RDS** | $85-100 | $200-250 | $650-800 | Production |
| **EC2 + RDS (On-Demand)** | $85-100 | $120-150 | $300-500 | Cost Control |
| **EC2 + RDS (Reserved)** | $70-85 | $100-130 | $250-400 | Long-term Savings |

---

## 💡 Cost Optimization Strategies

### 1. Use Reserved Instances (EC2/RDS)

**Savings:**
- 1-year reserved: **40% savings**
- 3-year reserved: **60% savings**

**Example:**
- EC2 t3.medium: $30/month → $18/month (1-year) → $12/month (3-year)
- RDS db.t3.small: $30/month → $18/month (1-year) → $12/month (3-year)

**Annual Savings:**
- EC2: $144/year (1-year) or $216/year (3-year)
- RDS: $144/year (1-year) or $216/year (3-year)
- **Total: $288-432/year**

### 2. Right-Size Your Resources

**Start Small, Scale Up:**
- Development: App Runner (1 vCPU, 2 GB) = $9/month
- Small Production: ECS (0.5 vCPU, 1 GB) = $35/month
- Medium Production: ECS (1 vCPU, 2 GB) = $70/month
- Large Production: ECS (2 vCPU, 4 GB) = $140/month

**Monitor and Adjust:**
- Use CloudWatch to track CPU/memory usage
- Scale down if consistently under 30% utilization
- Scale up if consistently over 70% utilization

### 3. Use Spot Instances (EC2 Only)

**Savings: Up to 90% off on-demand**

**Example:**
- t3.medium on-demand: $30/month
- t3.medium spot: $3-9/month (varies by availability)

**⚠️ Warning:** Spot instances can be terminated with 2-minute notice. Best for:
- Development environments
- Non-critical workloads
- Batch processing

### 4. Optimize Database

**RDS Optimization:**
- Use db.t3.micro for small apps: $15/month
- Upgrade to db.t3.small only when needed: $30/month
- Use reserved instances for 40-60% savings
- Enable automated backups (7 days free, then $0.095/GB)

**Storage Optimization:**
- Use gp3 instead of io1/io2 (cheaper)
- Monitor storage usage, delete old backups
- Use S3 for long-term backups instead of RDS

### 5. Reduce Data Transfer Costs

**Strategies:**
- Use CloudFront CDN (cheaper than direct transfer)
- Enable compression
- Cache static assets
- Use same region for all services

**CloudFront Pricing:**
- First 10 TB: $0.085/GB (US)
- Often cheaper than direct data transfer

### 6. Optimize CloudWatch Logs

**Strategies:**
- Set log retention (7 days vs 30 days)
- Filter logs (only log errors in production)
- Use log sampling for high-volume logs
- Archive old logs to S3 (cheaper)

**Savings:**
- 30-day retention: $5/month
- 7-day retention: $1.25/month
- **Save: $3.75/month**

### 7. Use S3 for Backups (Instead of RDS Only)

**Cost Comparison:**
- RDS backup storage: $0.095/GB-month
- S3 standard storage: $0.023/GB-month
- **Savings: 75%**

**Strategy:**
- Keep 7 days in RDS (free)
- Archive older backups to S3
- Restore from S3 when needed

---

## 📈 Cost Projections by Traffic Level

### Low Traffic (100-1,000 users/day)

| Option | Monthly Cost | Notes |
|--------|-------------|-------|
| App Runner | $15-25 | Simplest, good for MVP |
| ECS Fargate | $85-100 | Overkill, but production-ready |
| EC2 (reserved) | $70-85 | Good balance |

**Recommendation: App Runner ($15-25/month)**

---

### Medium Traffic (1,000-10,000 users/day)

| Option | Monthly Cost | Notes |
|--------|-------------|-------|
| App Runner | $50-100 | Can get expensive |
| ECS Fargate | $150-200 | Ideal for this level |
| EC2 (reserved) | $100-130 | Cost-effective |

**Recommendation: ECS Fargate or EC2 Reserved ($100-200/month)**

---

### High Traffic (10,000-100,000 users/day)

| Option | Monthly Cost | Notes |
|--------|-------------|-------|
| App Runner | $200-500 | Very expensive |
| ECS Fargate | $400-600 | Scales well |
| EC2 (reserved) | $300-500 | Most cost-effective |

**Recommendation: EC2 Reserved Instances ($300-500/month)**

---

### Very High Traffic (100,000+ users/day)

| Option | Monthly Cost | Notes |
|--------|-------------|-------|
| ECS Fargate | $800-2000 | Auto-scales |
| EC2 (reserved) | $600-1500 | Need auto-scaling group |

**Recommendation: ECS Fargate with auto-scaling ($800-2000/month)**

---

## 🎯 My Cost-Optimized Recommendations

### Phase 1: Launch (0-1,000 users/day)
**App Runner: $15-25/month**
- Simplest deployment
- No infrastructure management
- Good enough for initial launch

### Phase 2: Growth (1,000-10,000 users/day)
**ECS Fargate + RDS: $150-200/month**
- Production-grade
- Better performance
- Proper database management
- Auto-scaling

### Phase 3: Scale (10,000+ users/day)
**EC2 Reserved + RDS Reserved: $300-500/month**
- Maximum cost savings
- Full control
- Predictable costs
- 40-60% savings with reserved instances

---

## 💰 Additional AWS Services Costs

### AWS Bedrock (AI)
- **Claude 3 Sonnet**: 
  - Input: $0.003/1K tokens
  - Output: $0.015/1K tokens
  - **Estimated: $10-50/month** (depends on usage)

### AWS Secrets Manager
- **$0.40/secret/month**
- **$0.05/10K API calls**
- **Estimated: $1-5/month**

### CloudFront CDN
- **First 10 TB**: $0.085/GB (US)
- **Estimated: $5-20/month** (depends on traffic)

### S3 Storage
- **Standard**: $0.023/GB-month
- **Requests**: $0.005/1K PUT requests
- **Estimated: $1-5/month**

### Route 53 (DNS)
- **Hosted zone**: $0.50/month
- **Queries**: $0.40/million (first 1B free)
- **Estimated: $0.50-2/month**

---

## 📊 Total Cost of Ownership (TCO) - First Year

### Option 1: App Runner (MVP)
- **Year 1**: $180-300
- **Year 2**: $180-300
- **Best for**: Quick launch, low traffic

### Option 2: ECS Fargate + RDS
- **Year 1**: $1,200-2,400
- **Year 2**: $1,200-2,400
- **Best for**: Production, medium traffic

### Option 3: EC2 Reserved + RDS Reserved
- **Year 1**: $840-1,200 (1-year reserved)
- **Year 2-3**: $720-1,020 (3-year reserved)
- **Best for**: Long-term, cost optimization

---

## 🎯 Final Recommendation by Budget

### Budget: <$50/month
**Use: App Runner**
- Simple, managed
- Good for MVP/testing
- Can migrate later

### Budget: $50-150/month
**Use: ECS Fargate + RDS (db.t3.micro)**
- Production-ready
- Proper database
- Auto-scaling

### Budget: $150-300/month
**Use: ECS Fargate + RDS (db.t3.small)**
- Production-grade
- Better performance
- High availability

### Budget: $300+/month
**Use: EC2 Reserved + RDS Reserved**
- Maximum savings
- Full control
- Predictable costs

---

## 📝 Cost Monitoring Tips

1. **Set up AWS Budgets**
   - Alert at 50%, 80%, 100% of budget
   - Prevent surprise bills

2. **Use Cost Explorer**
   - Track spending by service
   - Identify cost drivers
   - Forecast future costs

3. **Tag Resources**
   - Track costs by environment (dev/staging/prod)
   - Identify unused resources

4. **Regular Reviews**
   - Monthly cost review
   - Right-size resources
   - Remove unused resources

---

## 🚨 Hidden Costs to Watch

1. **Data Transfer Out**: Can add $10-50/month
2. **CloudWatch Logs**: Can add $5-20/month if not managed
3. **RDS Backup Storage**: Can add $5-15/month
4. **ALB LCU**: Can add $5-20/month with high traffic
5. **EFS**: Can add $3-10/month

**Total Hidden Costs: $20-100/month** (if not optimized)

---

## ✅ Cost Optimization Checklist

- [ ] Use reserved instances for EC2/RDS (40-60% savings)
- [ ] Right-size resources (don't over-provision)
- [ ] Set CloudWatch log retention (7 days vs 30 days)
- [ ] Use S3 for long-term backups (75% cheaper)
- [ ] Enable CloudFront CDN (cheaper data transfer)
- [ ] Monitor and adjust auto-scaling
- [ ] Set up AWS Budgets alerts
- [ ] Tag all resources for cost tracking
- [ ] Review costs monthly
- [ ] Remove unused resources

---

## 📞 Need Help Estimating?

**Questions to Answer:**
1. Expected users per day?
2. Expected requests per second?
3. Database size (products, users)?
4. Data transfer volume?
5. Budget constraints?

**Based on your answers, I can provide a specific cost estimate!**

