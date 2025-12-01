# Tier Selection Guide: Users vs Tier Relationship

## 🎯 Understanding "Users" in Context

For InsightShop, we need to distinguish between:
1. **Monthly Visitors** - Total unique visitors to the store
2. **Registered Users** - Customers who created accounts
3. **Active Users** - Users who make purchases or interact regularly

**For tier selection, we primarily use Monthly Visitors as the key metric.**

---

## 📊 Tier Selection Matrix

### Tier 1: Starter (Small Shop)
**Best For: 0 - 1,000 Monthly Visitors**

| Monthly Visitors | Typical Shop Type | Why This Tier? |
|-----------------|-------------------|----------------|
| 0-100 | Just starting, testing | Low cost, all essential features |
| 100-500 | Small boutique, hobby shop | Handles traffic easily, affordable |
| 500-1,000 | Growing local business | Good value, room to grow |

**Product Limit:** Up to 500 products
**Visitor Limit:** Up to 1,000/month
**When to Upgrade:** When you consistently hit 800+ visitors/month

**Real-World Examples:**
- Small local boutique: 200-400 visitors/month
- Etsy seller expanding: 300-600 visitors/month
- New online store: 50-200 visitors/month
- Side business: 100-500 visitors/month

---

### Tier 2: Professional (Mid-Size Shop)
**Best For: 1,000 - 10,000 Monthly Visitors**

| Monthly Visitors | Typical Shop Type | Why This Tier? |
|-----------------|-------------------|----------------|
| 1,000-2,500 | Established local business | Need better AI, more products |
| 2,500-5,000 | Regional retailer | Advanced features, priority support |
| 5,000-10,000 | Growing e-commerce brand | Scale-ready, professional tools |

**Product Limit:** Up to 5,000 products
**Visitor Limit:** Up to 10,000/month
**When to Upgrade:** When you consistently hit 8,000+ visitors/month

**Real-World Examples:**
- Regional clothing store: 2,000-4,000 visitors/month
- Multi-brand retailer: 3,000-7,000 visitors/month
- Established boutique: 1,500-3,500 visitors/month
- Growing online brand: 5,000-8,000 visitors/month

---

### Tier 3: Enterprise (Large Shop)
**Best For: 10,000+ Monthly Visitors**

| Monthly Visitors | Typical Shop Type | Why This Tier? |
|-----------------|-------------------|----------------|
| 10,000-25,000 | Large retailer | Need unlimited scale, white-label |
| 25,000-50,000 | Multi-brand platform | Enterprise features, API access |
| 50,000+ | Major e-commerce | Custom needs, dedicated support |

**Product Limit:** Unlimited
**Visitor Limit:** Unlimited
**When to Consider:** When you need enterprise features regardless of traffic

**Real-World Examples:**
- Large fashion retailer: 20,000-40,000 visitors/month
- Multi-brand marketplace: 30,000-60,000 visitors/month
- National brand: 50,000+ visitors/month
- B2B wholesale platform: 10,000-30,000 visitors/month

---

## 📈 Traffic Growth Projection Model

### Typical Growth Pattern

```
Month 1-3:   50-200 visitors/month   → Starter
Month 4-6:   200-500 visitors/month  → Starter
Month 7-9:   500-1,000 visitors/month → Starter (approaching limit)
Month 10-12: 1,000-2,500 visitors/month → Professional
Year 2:      2,500-5,000 visitors/month → Professional
Year 3+:     5,000-10,000+ visitors/month → Professional/Enterprise
```

### Conversion Rate Impact

**Typical E-commerce Conversion Rates:**
- Starter shops: 1-2% (10-20 purchases per 1,000 visitors)
- Professional shops: 2-3% (20-30 purchases per 1,000 visitors)
- Enterprise shops: 2-4% (20-40 purchases per 1,000 visitors)

**Revenue Correlation:**
- 1,000 visitors/month × 2% conversion = 20 orders/month
- Average order value: $50-100
- Monthly revenue: $1,000-2,000
- **Tier cost ($99) = 5-10% of revenue** ✅ Good ratio

---

## 🧮 Tier Selection Formula

### Simple Formula

```
IF monthly_visitors < 1,000:
    → Starter Tier ($99/month)
    
ELIF monthly_visitors < 10,000:
    → Professional Tier ($299/month)
    
ELSE:
    → Enterprise Tier ($799/month)
```

### Advanced Formula (with other factors)

```
tier_score = 0

# Factor 1: Monthly Visitors (weight: 40%)
IF visitors < 500: tier_score += 1
ELIF visitors < 1,000: tier_score += 2
ELIF visitors < 5,000: tier_score += 3
ELIF visitors < 10,000: tier_score += 4
ELSE: tier_score += 5

# Factor 2: Products (weight: 25%)
IF products < 200: tier_score += 1
ELIF products < 500: tier_score += 2
ELIF products < 2,000: tier_score += 3
ELIF products < 5,000: tier_score += 4
ELSE: tier_score += 5

# Factor 3: Monthly Revenue (weight: 20%)
IF revenue < $1,000: tier_score += 1
ELIF revenue < $5,000: tier_score += 2
ELIF revenue < $15,000: tier_score += 3
ELIF revenue < $50,000: tier_score += 4
ELSE: tier_score += 5

# Factor 4: Support Needs (weight: 15%)
IF basic_support: tier_score += 1
ELIF priority_support: tier_score += 3
ELIF dedicated_support: tier_score += 5

# Tier Selection
IF tier_score <= 6: → Starter
ELIF tier_score <= 12: → Professional
ELSE: → Enterprise
```

---

## 📊 Decision Tree

```
START
  │
  ├─ Monthly Visitors?
  │   │
  │   ├─ < 1,000
  │   │   ├─ Products < 500? → Starter ✅
  │   │   └─ Products > 500? → Professional (or reduce products)
  │   │
  │   ├─ 1,000 - 10,000
  │   │   ├─ Products < 5,000? → Professional ✅
  │   │   └─ Products > 5,000? → Enterprise
  │   │
  │   └─ > 10,000
  │       └─ Enterprise ✅
  │
  └─ Need Enterprise Features?
      ├─ API Access? → Enterprise
      ├─ White-label? → Enterprise
      ├─ Unlimited users? → Enterprise
      └─ Dedicated support? → Enterprise
```

---

## 💡 Real-World Scenarios

### Scenario 1: New Online Boutique
- **Monthly Visitors:** 150
- **Products:** 80
- **Monthly Revenue:** $2,500
- **Recommendation:** Starter ($99/month)
- **Reason:** Low traffic, small catalog, cost-effective

### Scenario 2: Growing Fashion Store
- **Monthly Visitors:** 3,500
- **Products:** 1,200
- **Monthly Revenue:** $18,000
- **Recommendation:** Professional ($299/month)
- **Reason:** Good traffic, growing catalog, needs advanced features

### Scenario 3: Established Retailer
- **Monthly Visitors:** 25,000
- **Products:** 8,000
- **Monthly Revenue:** $150,000
- **Recommendation:** Enterprise ($799/month)
- **Reason:** High traffic, large catalog, needs enterprise features

### Scenario 4: Seasonal Business
- **Peak:** 5,000 visitors/month
- **Off-season:** 300 visitors/month
- **Recommendation:** Professional ($299/month)
- **Reason:** Average is ~2,650/month, Professional handles peak

---

## 📈 Traffic-to-Revenue Relationship

### Typical E-commerce Benchmarks

| Monthly Visitors | Conversion Rate | Orders/Month | Avg Order Value | Monthly Revenue | Tier |
|-----------------|----------------|--------------|-----------------|-----------------|------|
| 100 | 1.5% | 1.5 | $75 | $113 | Starter |
| 500 | 2% | 10 | $80 | $800 | Starter |
| 1,000 | 2% | 20 | $85 | $1,700 | Starter/Pro |
| 2,500 | 2.5% | 63 | $90 | $5,670 | Professional |
| 5,000 | 2.5% | 125 | $95 | $11,875 | Professional |
| 10,000 | 3% | 300 | $100 | $30,000 | Professional/Enterprise |
| 25,000 | 3% | 750 | $105 | $78,750 | Enterprise |
| 50,000 | 3.5% | 1,750 | $110 | $192,500 | Enterprise |

**Tier Cost as % of Revenue:**
- Starter ($99): 5-10% of revenue (healthy)
- Professional ($299): 2-5% of revenue (excellent)
- Enterprise ($799): 0.4-1% of revenue (minimal)

---

## 🎯 Tier Selection by User Type

### Individual Seller / Hobbyist
- **Visitors:** 50-300/month
- **Products:** 20-100
- **Tier:** Starter
- **Why:** Low volume, testing market

### Small Business Owner
- **Visitors:** 300-1,000/month
- **Products:** 100-500
- **Tier:** Starter
- **Why:** Growing but manageable

### Established Local Business
- **Visitors:** 1,000-5,000/month
- **Products:** 500-2,000
- **Tier:** Professional
- **Why:** Need advanced features, better support

### Regional Retailer
- **Visitors:** 5,000-15,000/month
- **Products:** 2,000-5,000
- **Tier:** Professional
- **Why:** Scale, priority support

### Large Retailer / Brand
- **Visitors:** 15,000+/month
- **Products:** 5,000+
- **Tier:** Enterprise
- **Why:** Unlimited scale, enterprise features

---

## 🔄 Upgrade Path Recommendations

### When to Upgrade from Starter → Professional

**Triggers:**
1. Consistently hitting 800+ visitors/month
2. Need more than 500 products
3. Need custom domain
4. Need priority support
5. Monthly revenue > $10,000

**Timing:** Upgrade when you hit 2-3 triggers

### When to Upgrade from Professional → Enterprise

**Triggers:**
1. Consistently hitting 8,000+ visitors/month
2. Need more than 5,000 products
3. Need API access
4. Need white-label
5. Need unlimited admin users
6. Monthly revenue > $50,000

**Timing:** Upgrade when you hit 2-3 triggers

---

## 📊 Traffic Capacity by Tier

### Starter Tier Capacity
- **Recommended:** Up to 1,000 visitors/month
- **Maximum (before issues):** ~1,500 visitors/month
- **Bottleneck:** App Runner resources, database size

### Professional Tier Capacity
- **Recommended:** 1,000-10,000 visitors/month
- **Maximum (before issues):** ~15,000 visitors/month
- **Bottleneck:** Database performance, AI API limits

### Enterprise Tier Capacity
- **Recommended:** 10,000+ visitors/month
- **Maximum:** 100,000+ visitors/month (with proper scaling)
- **Bottleneck:** None (unlimited scale)

---

## 💰 Cost-Per-Visitor Analysis

| Tier | Monthly Cost | Visitor Limit | Cost per 1,000 Visitors |
|------|-------------|---------------|------------------------|
| Starter | $99 | 1,000 | $99 |
| Professional | $299 | 10,000 | $29.90 |
| Enterprise | $799 | Unlimited | Variable |

**Insight:** Professional tier is most cost-effective per visitor at scale.

---

## 🎯 Quick Decision Guide

**Ask these questions:**

1. **How many visitors per month?**
   - < 1,000 → Starter
   - 1,000-10,000 → Professional
   - > 10,000 → Enterprise

2. **How many products?**
   - < 500 → Starter
   - 500-5,000 → Professional
   - > 5,000 → Enterprise

3. **Monthly revenue?**
   - < $5,000 → Starter
   - $5,000-50,000 → Professional
   - > $50,000 → Enterprise

4. **Need enterprise features?**
   - API, white-label, unlimited users → Enterprise
   - Otherwise → Use traffic/product limits

---

## 📝 Summary Table

| Monthly Visitors | Products | Monthly Revenue | Recommended Tier | Monthly Cost |
|-----------------|----------|-----------------|------------------|--------------|
| 0-500 | < 200 | < $5,000 | Starter | $99 |
| 500-1,000 | 200-500 | $5,000-10,000 | Starter | $99 |
| 1,000-2,500 | 500-1,500 | $10,000-25,000 | Professional | $299 |
| 2,500-5,000 | 1,500-3,000 | $25,000-50,000 | Professional | $299 |
| 5,000-10,000 | 3,000-5,000 | $50,000-100,000 | Professional | $299 |
| 10,000-25,000 | 5,000-10,000 | $100,000-250,000 | Enterprise | $799 |
| 25,000+ | 10,000+ | $250,000+ | Enterprise | $799 |

---

## 🚀 Growth Trajectory Example

**Year 1:**
- Month 1-3: 100 visitors → Starter
- Month 4-6: 400 visitors → Starter
- Month 7-9: 800 visitors → Starter (approaching limit)
- Month 10-12: 1,200 visitors → Upgrade to Professional

**Year 2:**
- Month 13-18: 2,000-4,000 visitors → Professional
- Month 19-24: 5,000-8,000 visitors → Professional

**Year 3:**
- Month 25-30: 10,000-15,000 visitors → Consider Enterprise
- Month 31-36: 20,000+ visitors → Enterprise

---

This guide helps customers choose the right tier based on their actual usage patterns!

