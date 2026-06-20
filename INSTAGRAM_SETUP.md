# Instagram Setup Guide — Trading Focus

## Account Setup
1. Go to: https://instagram.com
2. Create business account or convert existing
3. Go to: https://developers.facebook.com
4. Create app → Instagram Graph API
5. Get access token
6. Add to GitHub Secrets as `INSTAGRAM_ACCESS_TOKEN`

## Account Info Needed
- Instagram Business Account ID
- Add to GitHub Secrets as `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- Verify in Meta Business Suite: Settings → Instagram Accounts

## Profile Optimization

**Bio**: "AI Trading Strategies | 11-Strategy Engine | Backtests Inside"
**Link**: https://profitengine-tau.vercel.app (or Gumroad product URL)
**Profile Image**: ProfitEngine logo (professional, high contrast)
**Highlights**: 
- Backtests (carousel examples)
- Strategies (educational content)
- Results (backtest proof)

## Content Pillars (3-week rotation)

**Week 1: Strategies Deep Dives**
- Carousel (7 slides): Complete strategy breakdown (e.g., "Mean Reversion: Why It Works")
- Reel (60s): Strategy explainer with real chart examples
- Stories (3x/day): Market updates + poll + engagement questions

**Week 2: Backtesting Reality**
- Carousel (7 slides): Backtest vs live trading comparison
- Reel (60s): "Why your backtest is lying" with proof
- Stories (3x/day): Market conditions + strategy tips + community poll

**Week 3: Risk Management & Results**
- Carousel (7 slides): Risk framework or real case study
- Reel (60s): How to avoid backtest overfitting
- Stories (3x/day): Risk management tips + market setup + Q&A

## Posting Schedule

**Carousel Posts**: 3x per week (Tuesday 8 PM, Thursday 9 AM, Saturday 10 AM)
**Reels**: 3x per week (Wednesday 1 PM, Friday 12 PM, Sunday 6 PM)
**Stories**: Daily (8 AM, 1 PM, 6 PM — 3 stories total)

**Timing Strategy**:
- Reels get 67% higher reach — post mid-day
- Carousels get 40% higher engagement — post evening (desktop browsing)
- Stories drive cross-traffic — post 2x daily during peak hours

### Hashtag Strategy (Trading-Focused)

**Primary Hashtags** (use all 11):
- #TradingStrategy
- #Backtesting
- #AlgoTrading
- #FuturesTrading
- #DayTrading
- #TradingEdge
- #MeanReversion
- #MomentumTrading
- #TechAnalysis
- #TradersCommunity
- #StrategyBreakdown

**Mix**: 30% popular (100K+ posts), 40% medium (10K-100K), 30% niche (1K-10K)

**Avoid**: #FX, #Crypto, #GetRich (low engagement for trading strategies)

## Cross-Platform Workflow

### How Threads → Instagram Automation Works

```
Day 1 (Monday 9 AM ET):
├─ Publish Threads post with strategy breakdown
├─ Engage replies for 2 hours (100% reply rate)
├─ Generate carousel structure via /api/social/cross-post
└─ Generate reel script via same endpoint

Day 2 (Tuesday):
├─ Design carousel in Canva using slide structure
├─ Upload carousel slide images to cloud storage
├─ Get image URLs for all 7 slides
├─ POST to /api/social/instagram/carousel/publish
└─ Schedule posting for 8 PM ET

Day 3 (Wednesday):
├─ Record reel video (screen recording or AI video)
├─ Upload video to cloud storage
├─ Get video URL
├─ POST to /api/social/instagram/reel/publish
└─ Schedule posting for 1 PM ET

Day 4-7 (Engagement):
├─ Share carousel to Stories (promo)
├─ Mention carousel in reel captions
├─ Cross-reference back to original Threads post
├─ Reply to carousel/reel comments
└─ Share best comments on Stories
```

### API Endpoints

**Generate Carousel from Threads**:
```
POST /api/social/cross-post
{
  "platform": "threads",
  "content": "[Threads post text]",
  "strategy": "Mean Reversion",
  "type": "thread",
  "backtestData": {
    "returns": 28,
    "winRate": 55,
    "maxDrawdown": 8,
    "sharpeRatio": 1.8,
    "trades": 45,
    "period": "6 months"
  }
}
```

**Get Carousel Preview**:
```
GET /api/social/cross-post?threadText=[URL-encoded text]&strategy=Mean Reversion
```

**Publish Carousel**:
```
PUT /api/social/instagram/carousel/publish
{
  "carouselId": "carousel-123",
  "slides": [
    { "imageUrl": "https://..." },
    { "imageUrl": "https://..." }
  ],
  "caption": "[7-slide carousel caption]"
}
```

**Publish Reel**:
```
PUT /api/social/instagram/reel/publish
{
  "reelId": "reel-123",
  "videoUrl": "https://video.mp4",
  "caption": "[Reel caption]"
}
```

## Growth Targets

- **Month 1**: 100-200 followers (launch, niche audience)
- **Month 2**: 300-500 followers (content consistency, algorithm boost)
- **Month 3**: 800-1,200 followers (carousel + reel synergy)
- **Month 6**: 2,000-3,000 followers (cross-platform promotion)
- **Year 1**: 5,000-8,000 followers (trading community maturity)

## Monetization

**Primary**: Link in bio → ProfitEngine free trial
**Secondary**: Affiliate links in carousel captions (with #ad disclosure)
**Tertiary**: Lead generation for prop trading job referrals
**Target Revenue**: $200-500/month from Instagram referrals

## FTC Compliance

**Required**:
- All posts with affiliate links must include #ad or #sponsored in first line
- Carousel caption mentions "ProfitEngine" = affiliate/business relationship
- Stories with product mentions = #ad required
- No fake results — all backtests must be labeled "backtesting results"

**Auto-Injected**: 
- FTC disclosure appears on carousel final slide
- Reel captions include affiliate link disclaimer
- All metrics clearly labeled (e.g., "Backtest: 28% annual | Live: 12%")

## Performance Tracking

**Track Weekly**:
- Impressions (target: 5K-10K/week)
- Engagement rate (target: 8-12%)
- Saves (target: 15-25% of impressions)
- Link clicks (target: 2-5% CTR)
- New followers (target: 30-50/week)

**Track Monthly**:
- Follower growth trend
- Reel vs carousel reach (expect 67% higher for reels)
- Best-performing hashtags
- Best posting times for your audience
- Traffic to ProfitEngine from Instagram

