# Affiliate Tracking Dashboard & Analytics

Complete guide to tracking affiliate revenue, attributing conversions, and optimizing performance.

---

## Overview

**Goal**: Track every click and conversion, identify which content drives revenue, and optimize placement and messaging.

**Key Metrics to Track**:
- Total clicks per partner (funnel entry)
- Click-to-signup rate (conversion efficiency)
- Revenue per partner (absolute value)
- Revenue per content piece (ROI of content)
- Time-to-conversion (how long between click and signup)
- Repeat customers (high-value users)

---

## 1. Setup & Infrastructure

### 1.1 Database Schema (PostgreSQL / MongoDB)

#### PostgreSQL Option

```sql
-- Affiliate click events (raw data)
CREATE TABLE affiliate_clicks (
  id SERIAL PRIMARY KEY,
  partner_id VARCHAR(50) NOT NULL,
  source VARCHAR(255) NOT NULL,           -- 'blog-post-iron-condor', 'youtube-tutorial', etc.
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  user_agent TEXT,
  referrer TEXT,
  session_id VARCHAR(255),
  user_id UUID REFERENCES users(id),
  
  INDEX idx_partner_timestamp (partner_id, timestamp),
  INDEX idx_source_timestamp (source, timestamp)
);

-- Affiliate conversions (signups/purchases)
CREATE TABLE affiliate_conversions (
  id SERIAL PRIMARY KEY,
  affiliate_click_id INTEGER REFERENCES affiliate_clicks(id),
  partner_id VARCHAR(50) NOT NULL,
  source VARCHAR(255),
  revenue_usd DECIMAL(10, 2),
  conversion_type VARCHAR(50),           -- 'signup', 'purchase', 'subscription'
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  user_id UUID REFERENCES users(id),
  customer_id VARCHAR(255),
  notes TEXT,
  
  INDEX idx_partner_timestamp (partner_id, timestamp),
  INDEX idx_revenue (revenue_usd)
);

-- Monthly revenue summary (for fast dashboard queries)
CREATE TABLE affiliate_revenue_summary (
  id SERIAL PRIMARY KEY,
  partner_id VARCHAR(50) NOT NULL,
  month DATE NOT NULL,
  total_clicks INTEGER DEFAULT 0,
  total_conversions INTEGER DEFAULT 0,
  total_revenue_usd DECIMAL(10, 2) DEFAULT 0,
  conversion_rate DECIMAL(5, 4),        -- e.g., 0.0850 = 8.5%
  average_revenue_per_conversion DECIMAL(10, 2),
  
  UNIQUE(partner_id, month)
);
```

#### MongoDB Option

```javascript
// Affiliate events collection
db.createCollection('affiliate_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['partner', 'source', 'timestamp', 'type'],
      properties: {
        _id: { bsonType: 'objectId' },
        type: { enum: ['click', 'conversion'] },
        partner: { bsonType: 'string' },
        source: { bsonType: 'string' },
        timestamp: { bsonType: 'date' },
        revenue: { bsonType: 'decimal128' },
        conversionType: { bsonType: 'string' },
        userId: { bsonType: 'string' },
        sessionId: { bsonType: 'string' },
      }
    }
  }
});

// Create indexes
db.affiliate_events.createIndex({ partner: 1, timestamp: 1 });
db.affiliate_events.createIndex({ source: 1, timestamp: 1 });
db.affiliate_events.createIndex({ timestamp: 1 });
```

### 1.2 API Route for Click Tracking

**Endpoint**: `POST /api/affiliate/track`

```typescript
// app/api/affiliate/track.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      partnerId,
      source,
      userId,
    } = body;

    // Validate
    if (!partnerId || !source) {
      return NextResponse.json(
        { error: 'Missing partnerId or source' },
        { status: 400 }
      );
    }

    // Get session/cookie data
    const sessionId = req.cookies.get('session_id')?.value;
    const userAgent = req.headers.get('user-agent') || 'unknown';
    const referrer = req.headers.get('referer') || 'direct';

    // Record in database
    // await db.collection('affiliate_events').insertOne({
    //   type: 'click',
    //   partner: partnerId,
    //   source: source,
    //   timestamp: new Date(),
    //   sessionId,
    //   userId,
    //   userAgent,
    //   referrer,
    // });

    return NextResponse.json({
      success: true,
      tracked: true,
    });
  } catch (error) {
    console.error('Affiliate tracking error:', error);
    return NextResponse.json(
      { error: 'Tracking failed' },
      { status: 500 }
    );
  }
}
```

---

## 2. Google Sheets Tracking Template

**Best for**: Early stage when traffic is low and database is overkill.

### 2.1 Daily Affiliate Log

Create a Google Sheet with this structure:

| Date | Partner | Source | Clicks | Conversions | Revenue | Notes |
|------|---------|--------|--------|---|---|---|
| 2024-06-20 | Interactive Brokers | blog-iron-condor | 12 | 1 | $50 | Search traffic |
| 2024-06-20 | Tastytrade | youtube-tutorial | 8 | 0 | $0 | Video posted |
| 2024-06-21 | TradingView | newsletter | 45 | 5 | $25 | Email blast |

**Formula for Conversion Rate** (column F):
```
=IF(D2>0, E2/D2, 0)
```

**Formula for Revenue per Click**:
```
=IF(D2>0, F2/D2, 0)
```

### 2.2 Monthly Summary Sheet

| Partner | Clicks | Conversions | Conversion % | Total Revenue | Avg/Conversion | Rank |
|---------|--------|---|---|---|---|---|
| Interactive Brokers | 145 | 14 | 9.7% | $700 | $50 | 1 |
| Tastytrade | 102 | 7 | 6.9% | $350 | $50 | 2 |
| TradingView | 234 | 18 | 7.7% | $90 | $5 | 3 |
| Polygon.io | 45 | 8 | 17.8% | $240 | $30 | 4 |

**Pull monthly data with formulas**:
```
=SUMIF('Daily Log'!B:B, "Interactive Brokers", 'Daily Log'!D:D)  // Total clicks
=SUMIF('Daily Log'!B:B, "Interactive Brokers", 'Daily Log'!E:E)  // Total conversions
```

### 2.3 Content Performance Sheet

Track which blog posts / videos drive the most affiliate revenue.

| Content Title | Type | Date | Partners | Clicks | Conversions | Revenue |
|---|---|---|---|---|---|---|
| Iron Condor Complete Guide | Blog | 2024-06-01 | IBKR, Tastytrade, OptionStrat | 245 | 22 | $1,350 |
| Getting Started with ThinkorSwim | Video | 2024-06-05 | ThinkorSwim, TradingView | 567 | 18 | $240 |
| Advanced Options Strategies | Blog | 2024-06-12 | IBKR, Polygon | 189 | 28 | $1,240 |
| Options Trading Psychology | Article | 2024-06-15 | Udemy, Gumroad | 92 | 6 | $190 |

---

## 3. Dashboard Queries

### 3.1 SQL Queries for Analytics

**Total clicks by partner (last 30 days)**:
```sql
SELECT 
  partner_id,
  COUNT(*) as total_clicks,
  COUNT(DISTINCT DATE(timestamp)) as active_days
FROM affiliate_clicks
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY partner_id
ORDER BY total_clicks DESC;
```

**Conversion funnel (by partner)**:
```sql
SELECT 
  c.partner_id,
  COUNT(DISTINCT c.session_id) as total_sessions,
  COUNT(DISTINCT CASE WHEN conv.id IS NOT NULL THEN c.id END) as conversions,
  ROUND(
    COUNT(DISTINCT CASE WHEN conv.id IS NOT NULL THEN c.id END)::numeric 
    / COUNT(DISTINCT c.session_id) * 100, 
    2
  ) as conversion_rate
FROM affiliate_clicks c
LEFT JOIN affiliate_conversions conv 
  ON c.id = conv.affiliate_click_id
WHERE c.timestamp >= NOW() - INTERVAL '30 days'
GROUP BY c.partner_id
ORDER BY conversion_rate DESC;
```

**Revenue by content source (last 30 days)**:
```sql
SELECT 
  source,
  COUNT(*) as clicks,
  COUNT(DISTINCT user_id) as unique_users,
  SUM(COALESCE(c.revenue_usd, 0)) as total_revenue,
  ROUND(AVG(COALESCE(c.revenue_usd, 0)), 2) as avg_revenue_per_click
FROM affiliate_clicks ac
LEFT JOIN affiliate_conversions c 
  ON ac.id = c.affiliate_click_id
WHERE ac.timestamp >= NOW() - INTERVAL '30 days'
GROUP BY source
ORDER BY total_revenue DESC;
```

**Best performing content (ROI)**:
```sql
SELECT 
  source,
  SUM(COALESCE(c.revenue_usd, 0)) as total_revenue,
  COUNT(*) as clicks,
  ROUND(SUM(COALESCE(c.revenue_usd, 0))::numeric / COUNT(*), 2) as revenue_per_click
FROM affiliate_clicks ac
LEFT JOIN affiliate_conversions c 
  ON ac.id = c.affiliate_click_id
WHERE ac.timestamp >= NOW() - INTERVAL '90 days'
GROUP BY source
HAVING SUM(COALESCE(c.revenue_usd, 0)) > 0
ORDER BY revenue_per_click DESC;
```

### 3.2 MongoDB Aggregation Queries

**Total revenue by partner (last 30 days)**:
```javascript
db.affiliate_events.aggregate([
  {
    $match: {
      timestamp: { $gte: new Date(Date.now() - 30*24*60*60*1000) },
      type: 'conversion'
    }
  },
  {
    $group: {
      _id: '$partner',
      totalRevenue: { $sum: { $toDouble: '$revenue' } },
      conversionCount: { $sum: 1 }
    }
  },
  { $sort: { totalRevenue: -1 } }
])
```

**Conversion funnel by content source**:
```javascript
db.affiliate_events.aggregate([
  {
    $match: {
      timestamp: { $gte: new Date(Date.now() - 30*24*60*60*1000) }
    }
  },
  {
    $group: {
      _id: { source: '$source', type: '$type' },
      count: { $sum: 1 }
    }
  },
  { $sort: { '_id.source': 1, '_id.type': 1 } }
])
```

---

## 4. Monthly Review Checklist

**Perform this every month to identify optimization opportunities**:

- [ ] **Total revenue**: Compare to target ($1,281/month at scale)
- [ ] **Top 3 partners by revenue**: Are they the expected ones?
- [ ] **Lowest-performing partners**: Should we deprioritize or reposition?
- [ ] **Best-performing content**: Which posts/videos drive the most conversions?
- [ ] **Engagement by channel**: Email vs. blog vs. social vs. YouTube?
- [ ] **Conversion rates**: Which partners have >10% conversion? Which are <5%?
- [ ] **Revenue per click**: Which content pieces are most efficient?
- [ ] **New opportunities**: Any partners with high click volume but low conversions?
- [ ] **Messaging test**: Try new CTAs or positioning in underperforming pieces
- [ ] **FTC compliance**: Are all links properly disclosed?

---

## 5. Example Dashboard (Vercel Analytics Integration)

Use Vercel Analytics to track affiliate links automatically.

```typescript
// app/components/AffiliateDashboard.tsx
'use client';

import { useEffect, useState } from 'react';

export default function AffiliateDashboard() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    // Fetch affiliate stats from API
    fetch('/api/affiliate/stats?days=30')
      .then((r) => r.json())
      .then((data) => setStats(data))
      .catch(console.error);
  }, []);

  if (!stats) return <div>Loading dashboard...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Affiliate Performance (Last 30 Days)</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '16px' }}>
        <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', color: '#666' }}>Total Clicks</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.totalClicks}</div>
        </div>

        <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', color: '#666' }}>Conversions</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.totalConversions}</div>
        </div>

        <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', color: '#666' }}>Total Revenue</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4CAF50' }}>
            ${stats.totalRevenue.toFixed(2)}
          </div>
        </div>

        <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', color: '#666' }}>Conversion Rate</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {(stats.conversionRate * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      <h2 style={{ marginTop: '32px' }}>Revenue by Partner</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #ccc' }}>
            <th style={{ textAlign: 'left', padding: '8px' }}>Partner</th>
            <th style={{ textAlign: 'right', padding: '8px' }}>Clicks</th>
            <th style={{ textAlign: 'right', padding: '8px' }}>Conversions</th>
            <th style={{ textAlign: 'right', padding: '8px' }}>Revenue</th>
            <th style={{ textAlign: 'right', padding: '8px' }}>Conv Rate</th>
          </tr>
        </thead>
        <tbody>
          {stats.byPartner.map((row: any) => (
            <tr key={row.partner} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '8px' }}>{row.partner}</td>
              <td style={{ textAlign: 'right', padding: '8px' }}>{row.clicks}</td>
              <td style={{ textAlign: 'right', padding: '8px' }}>{row.conversions}</td>
              <td style={{ textAlign: 'right', padding: '8px' }}>${row.revenue.toFixed(2)}</td>
              <td style={{ textAlign: 'right', padding: '8px' }}>
                {((row.conversions / row.clicks) * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ marginTop: '32px' }}>Top Content by Revenue</h2>
      <ul>
        {stats.topContent.map((content: any) => (
          <li key={content.source}>
            <strong>{content.source}</strong> — ${content.revenue.toFixed(2)} ({content.conversions} conversions)
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 6. A/B Testing Framework

### 6.1 Test Ideas

Test different CTAs and positioning to optimize conversion rates:

| Test | Variable | Control | Variant | Duration | Success Metric |
|------|----------|---------|---------|----------|---|
| CTA Text | Button text | "Learn More" | "Get Started Free" | 2 weeks | +5% CTR |
| Link Color | Visual | Blue (#0066cc) | Green (#48bb78) | 2 weeks | +3% CTR |
| Placement | Position | End of post | After first strategy | 2 weeks | +10% conversions |
| Messaging | Pitch | "Top-rated platform" | "Used by 1M+ traders" | 2 weeks | +8% conversion rate |
| Timing | When | All posts | Only first mention | 2 weeks | Monitor cannibalization |

### 6.2 Running an A/B Test

```typescript
// Variant: randomly split traffic
function getVariant(userId: string, testId: string): 'control' | 'variant' {
  // Deterministic hash so same user always sees same variant
  const hash = hashUserId(userId + testId) % 2;
  return hash === 0 ? 'control' : 'variant';
}

// Track variant impression
function trackVariant(userId: string, testId: string, partner: string, conversion: boolean) {
  const variant = getVariant(userId, testId);
  
  fetch('/api/affiliate/test', {
    method: 'POST',
    body: JSON.stringify({
      testId,
      variant,
      partner,
      conversion,
      userId,
      timestamp: new Date(),
    }),
  });
}

// Analyze results (after 2 weeks)
// SELECT 
//   variant, 
//   COUNT(*) as impressions,
//   SUM(CASE WHEN conversion THEN 1 ELSE 0 END) as conversions,
//   (SUM(CASE WHEN conversion THEN 1 ELSE 0 END) / COUNT(*)) as rate
// FROM affiliate_tests
// WHERE test_id = 'cta_button_test'
// GROUP BY variant;
```

---

## 7. Optimization Workflow

**Weekly optimization loop**:

1. **Monday**: Check dashboard — identify any drop-offs or new opportunities
2. **Tuesday**: Create 1–2 optimization experiments (test new CTA, reposition link, etc.)
3. **Wednesday–Friday**: Monitor test results; adjust messaging if needed
4. **Next Monday**: Analyze results; roll out winning variant

**Example optimization cycle**:

```
Week 1:
  - Notice: Blog post "Iron Condor" has 120 clicks, 4 conversions (3.3% rate)
  - Hypothesis: CTA "Learn More" is weak; try "Try Risk-Free"
  - Action: Deploy variant to 50% of traffic

Week 2:
  - Result: Variant gets 5% conversion rate (+51% improvement!)
  - Decision: Roll out to 100%, update all similar posts
  - Impact: +2 extra conversions/week = +$100/month
```

---

## 8. Revenue Attribution Models

### 8.1 Last-Click Attribution (Default)

Credit the last affiliate link clicked before conversion.

**Pros**: Simple, aligns with most affiliate networks
**Cons**: Ignores earlier touchpoints, undervalues awareness content

### 8.2 First-Click Attribution

Credit the first affiliate link that brought user into funnel.

**Pros**: Values top-of-funnel content
**Cons**: Ignores decision-stage content that actually closes deals

### 8.3 Linear Attribution

Split credit equally across all clicks in conversion journey.

**Pros**: Gives credit to all touchpoints
**Cons**: Complex to implement, harder to optimize

### 8.4 Time-Decay Attribution (Recommended)

Weight recent clicks more heavily:
- Click 1 (days ago): 10% credit
- Click 2 (hours ago): 40% credit
- Click 3 (minutes ago): 50% credit

**Implementation**:
```typescript
function calculateTimeDecayAttribution(clicks: Array<{timestamp: Date, partner: string}>) {
  const now = new Date();
  const weights = clicks.map((click, index) => {
    const minutesSince = (now.getTime() - click.timestamp.getTime()) / 60000;
    // Exponential decay: more recent = higher weight
    return Math.exp(-minutesSince / 1440); // 1 day half-life
  });
  
  const total = weights.reduce((a, b) => a + b, 0);
  
  return clicks.map((click, i) => ({
    partner: click.partner,
    credit: weights[i] / total, // Normalized 0–1
  }));
}
```

---

## 9. Monthly Report Template

**Send to stakeholders at end of each month**:

```markdown
# Affiliate Revenue Report — June 2024

## Executive Summary
- **Total Clicks**: 892
- **Total Conversions**: 72
- **Conversion Rate**: 8.1%
- **Total Revenue**: $1,847
- **Monthly Target**: $1,281
- **Status**: ✅ **+44% above target**

## By Partner

| Partner | Clicks | Conversions | Revenue | Growth |
|---------|--------|---|---|---|
| Interactive Brokers | 145 | 14 | $700 | +25% |
| Polygon.io | 134 | 22 | $540 | +40% |
| Tastytrade | 102 | 7 | $350 | -10% |

## Top Content
1. **Blog: Iron Condor Strategy** — $480 revenue (54 clicks, 9 conversions)
2. **Video: Advanced Options** — $420 revenue (89 clicks, 12 conversions)
3. **Newsletter: June Tips** — $347 revenue (192 clicks, 8 conversions)

## Insights & Next Steps
- **Opportunity**: Blog posts underperforming vs. YouTube; invest more in video
- **Watch**: Tastytrade declining; test new messaging next month
- **Action**: Scale "Iron Condor" content (highest-converting); republish on social

---

*Next review: July 31, 2024*
```

---

## 10. Tools & Integrations

### 10.1 Recommended Analytics Platforms

| Tool | Best For | Cost | Notes |
|------|----------|------|-------|
| Google Analytics 4 | Web traffic attribution | Free | Affiliate links tracked automatically |
| Vercel Analytics | Web vitals + conversion tracking | Free | Built-in for Vercel deployments |
| Stripe (Affiliate Module) | E-commerce conversion tracking | 2.9% + $0.30 | If selling through Stripe |
| Impact.com | Multi-partner affiliate network | 10–30% fee | All partners in one dashboard |
| Refersion | Shopify affiliate tracking | Free–$$$ | Integrates with stores |
| Kenshoo | Advanced attribution modeling | $$$$ | Enterprise-level analysis |

### 10.2 UTM Parameter Structure

Every affiliate link should include UTM parameters for tracking:

```
https://partner.com/path?
  utm_source=profitengine-{PARTNER_ID}
  &utm_medium=affiliate
  &utm_campaign={CONTENT_SOURCE}
  &utm_content={VARIANT}
  &utm_term={KEYWORD}
```

**Example**:
```
https://alpaca.markets?
  utm_source=profitengine-alpaca
  &utm_medium=affiliate
  &utm_campaign=blog-trading-bots
  &utm_content=cta-button
  &utm_term=algorithmic-trading
```

---

## 11. Troubleshooting

### "Revenue isn't tracking properly"

1. Check database: Is click event being recorded?
   ```sql
   SELECT COUNT(*) FROM affiliate_clicks WHERE timestamp >= NOW() - INTERVAL '1 day';
   ```

2. Check affiliate partner: Are they reporting revenue to their dashboard?
   - Log into partner's affiliate dashboard
   - Verify your tracking link is correct
   - Check for cookie windows (some are only 7 days)

3. Check conversion attribution: Did the user click affiliate link → sign up on same device/browser?
   - Cross-device conversions are often not attributed
   - Some partners only track same-browser

### "One partner is suddenly getting zero clicks"

Likely causes:
- Link is broken (404 error) → Test the link
- Partner changed their domain → Update your links
- Seasonal drop in traffic → Check Google Analytics traffic overall
- Link was deactivated by partner → Check partner affiliate dashboard

### "Conversion rate is 0% for a partner"

1. Clicks are being tracked, but conversions aren't recorded
2. Check if partner reports via postback URL (real-time) or daily export (delay)
3. Verify conversion cookie window (some partners only track 7-day window)
4. Test the flow manually: Click link → does it reach partner? → Can you sign up?

---

## 12. Scaling Recommendations

**At $500/month revenue**: Keep Google Sheets; start exploring database

**At $1K/month revenue**: Migrate to PostgreSQL or MongoDB; build dashboard

**At $5K/month revenue**: Implement real-time analytics; A/B test infrastructure

**At $10K/month revenue**: Hire affiliate manager; consider affiliate network (Impact.com)

**At $50K+/month revenue**: Multi-channel attribution modeling; predictive analytics
