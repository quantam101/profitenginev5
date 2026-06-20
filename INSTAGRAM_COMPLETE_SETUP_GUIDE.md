# INSTAGRAM COMPLETE SETUP GUIDE — STEP-BY-STEP

**Objective**: Set up Instagram account, generate first posts, verify functionality  
**Timeline**: 2-3 hours total  
**Account Type**: BUSINESS (required for analytics, contact buttons, checkout)  

---

## PART 1: CHOOSE ACCOUNT TYPE (5 minutes)

### **CREATOR vs BUSINESS ACCOUNT**

| Feature | Creator | Business |
|---------|---------|----------|
| **Monetization** | Badges, subscriptions | Badges, subscriptions, checkout |
| **Analytics** | Basic | Advanced (reach, engagement, demographics) |
| **Contact Button** | Email link | Email, DM, call, website |
| **Shopping** | No | Yes (product checkout) |
| **Ad Tools** | Limited | Full suite |
| **Best For** | Personalities | Brands, products, services |

**RECOMMENDATION FOR PROFITENGINE**: ✅ **BUSINESS ACCOUNT**

**Why**:
- Need advanced analytics to track post performance
- Will link to premium product ($29/mo subscription)
- Want contact buttons for outreach
- Need checkout for affiliate → product funnel
- Can run ads later

---

## PART 2: CREATE BUSINESS ACCOUNT (10 minutes)

### **STEP 1: Convert or Create Account**

**If you have existing Instagram account:**
1. Open Instagram mobile app or web
2. Go to Profile → Settings → Account type and tools
3. Click "Switch to professional account"
4. Select "Business"
5. Choose category: "Professional Services" or "Financial Services"
6. Add business details:
   - Business name: "ProfitEngine" or "Already Here LLC"
   - Website: https://profitengine-tau.vercel.app
   - Contact email: dispatch@alreadyherellc.com
   - Phone: (optional)

**If creating new account:**
1. Sign up at instagram.com
2. Choose username: @profitengine or @profitenginetrading
3. Complete profile setup
4. Switch to business account (steps above)

### **STEP 2: Optimize Profile**

**Bio:**
```
🤖 11 Automated Trading Strategies
💰 Real Backtest Proof | $39K+ in Signals
📊 Free Trial Inside
🔗 Link in bio for live trading setup
```

**Website Link:** https://profitengine-tau.vercel.app/trading-free-trial

**Profile Picture:**
- Download trading/algorithm visual
- Recommended: Robot, chart, rocket, or lightning bolt
- Size: 110x110px minimum
- File: PNG with transparent background

**Name (first line of profile):**
```
ProfitEngine v5
```

---

## PART 3: SETUP INSTAGRAM GRAPH API (15 minutes)

### **STEP 1: Create Facebook App**

1. Go to https://developers.facebook.com
2. Click "Create App" (top right)
3. Fill form:
   - **App Name**: "ProfitEngine Instagram Bot"
   - **App Purpose**: Select "Business"
   - **Business Account**: Select your business (or create new)
4. Click "Create App"

### **STEP 2: Add Instagram Graph API**

1. In app dashboard, click "Add Product"
2. Search for "Instagram Graph API"
3. Click "Add"
4. Accept terms

### **STEP 3: Get Access Token**

1. In left sidebar, go to "Roles" → "Your Roles"
2. Confirm you're the app owner
3. Go to "Instagram" → "Basic Display"
4. Click "Get Started"
5. Select your Instagram account
6. Copy the **User ID** (you'll need this)
7. Now go to "Instagram Graph API" → "Tools"
8. Generate **User Access Token**:
   - Click "Generate Token"
   - Select your account
   - Approve permissions:
     - instagram_basic
     - instagram_graph_user_content
     - instagram_graph_user_media
   - Copy the token (save it!)

### **STEP 4: Convert to Long-Lived Token** (optional but recommended)

1. Go to https://graph.instagram.com/access_token
2. Input your user access token + app secret
3. Get long-lived token (expires in 60 days instead of 1 hour)
4. Save this token

---

## PART 4: ADD CREDENTIALS TO GITHUB SECRETS (10 minutes)

### **STEP 1: Get Your Instagram Business Account ID**

1. In Instagram Graph API Tools, you have:
   - User ID (your personal account)
   - Business Account ID (for your business profile)

2. If you need Business Account ID:
   ```bash
   curl "https://graph.instagram.com/me?fields=ig_user_id&access_token=YOUR_ACCESS_TOKEN"
   ```
   - This returns your IG User ID (format: 123456789)

### **STEP 2: Add to GitHub Secrets**

1. Go to your repo: https://github.com/quantam101/profitenginev5
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"

**Add these 3 secrets:**

| Secret Name | Value | Example |
|------------|-------|---------|
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Your IG User ID | `123456789` |
| `INSTAGRAM_ACCESS_TOKEN` | Your access token | `IGQVJv...` |
| `INSTAGRAM_GRAPH_API_VERSION` | Latest version | `v18.0` |

**Steps to add each:**
1. Secret name: (from table above)
2. Secret value: (your actual value)
3. Click "Add secret"
4. Repeat for all 3

---

## PART 5: VERIFY INSTAGRAM API WORKS (5 minutes)

### **STEP 1: Test API Connection**

Run this test to verify credentials work:

```bash
curl -X GET "https://graph.instagram.com/me?fields=username,name,biography,ig_user_id&access_token=YOUR_ACCESS_TOKEN"
```

Expected response:
```json
{
  "username": "profitengine",
  "name": "ProfitEngine v5",
  "biography": "11 Automated Trading Strategies...",
  "ig_user_id": "123456789",
  "id": "123456789"
}
```

If you see an error, go back to Part 3 and verify token/ID.

### **STEP 2: Verify GitHub Secrets**

1. Go to repo Settings → Secrets
2. Confirm all 3 secrets are added ✅
3. They should show as "Last updated X minutes ago"

---

## PART 6: GENERATE YOUR FIRST CAROUSEL POST (45 minutes)

### **STEP 1: Pick a Threads Post**

From `CONTENT_CALENDAR_MONTHLY.md`, pick one of the 17 posts. Example:

**Post 1: "The 11-Strategy System That Runs While You Sleep"**

Threads content:
```
Hook: 90% of retail traders watch charts. Top 10% automate it.
Body: Quick overview of 11 strategies + edge of diversification
Link: Landing page → free backtest guide
```

### **STEP 2: Generate Carousel Structure**

Run this API call (or use Postman/curl):

```bash
curl -X POST "http://localhost:3000/api/social/instagram/carousel" \
  -H "Content-Type: application/json" \
  -d '{
    "threadText": "90% of retail traders watch charts. Top 10% automate it. Here are the 11 strategies that run while you sleep...",
    "strategy": "Multi-Strategy Framework",
    "backtestData": {
      "totalProfit": 50000,
      "totalTrades": 77,
      "winRate": 0.45,
      "bestStrategy": "Mean Reversion",
      "bestPerformance": 39308.41
    }
  }'
```

Expected response:
```json
{
  "slides": [
    {
      "slideNumber": 1,
      "title": "Most Traders Do This Wrong",
      "keyPoints": ["90% watch charts manually", "4-8 hours/day", "Still lose money"],
      "visualDescription": "Text overlay on chart background"
    },
    {
      "slideNumber": 2,
      "title": "Automation Changes Everything",
      "keyPoints": ["Runs 24/7", "Removes emotion", "Manages risk automatically"],
      "visualDescription": "Robot with trading dashboard"
    },
    ...
  ],
  "caption": "11 Automated Trading Strategies That Never Sleep\n\nMost traders...",
  "hashtags": ["#Trading", "#AlgoTrading", ...]
}
```

### **STEP 3: Design Carousel Slides in Canva**

1. Go to https://www.canva.com
2. Create "Instagram Post" (1080x1350px)
3. For each slide from Step 2:
   - Title: Use slide title
   - Key points: 3-4 bullet points
   - Background: Trading chart or gradient
   - Text color: White on dark background
4. Export as image (PNG)
5. Save as: `slide-1.png`, `slide-2.png`, etc.

**Example Slide 1:**
```
TITLE: "Most Traders Do This Wrong"

• 90% watch charts manually
• 4-8 hours per day
• Still lose money consistently

[Dark background with faded chart]
```

### **STEP 4: Upload Carousel to Instagram**

#### **Option A: Manual (Easiest for first post)**

1. Open Instagram mobile app or web
2. Click "+" (Create)
3. Select "Post"
4. Click "Select multiple"
5. Upload your carousel slides in order (slide-1, slide-2, etc.)
6. Add caption from Step 2 response
7. Add hashtags
8. Post to Feed

#### **Option B: Using API (Automated)**

```bash
curl -X PUT "http://localhost:3000/api/social/instagram/carousel/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "slides": [
      {
        "imageUrl": "https://your-cdn.com/slide-1.png",
        "caption": "Part 1: Introduction"
      },
      {
        "imageUrl": "https://your-cdn.com/slide-2.png",
        "caption": "Part 2: Main content"
      }
    ],
    "caption": "11 Automated Trading Strategies...",
    "hashtags": ["#Trading", "#AlgoTrading", ...],
    "accessToken": "YOUR_INSTAGRAM_ACCESS_TOKEN"
  }'
```

---

## PART 7: GENERATE FIRST REEL (1 hour)

### **STEP 1: Generate Reel Script**

```bash
curl -X POST "http://localhost:3000/api/social/instagram/reel" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Mean Reversion: The Strategy Making $39K in Backtests",
    "duration": 60,
    "tone": "educational"
  }'
```

Expected response:
```json
{
  "segments": [
    {
      "segmentNumber": 1,
      "duration": 5,
      "title": "Hook",
      "voiceover": "Your backtest shows 30% returns. Your live account is down 12%. Here's why backtests lie to you.",
      "textOverlays": [
        {
          "text": "Backtest: +30%",
          "position": "top",
          "timing": "0-5s"
        }
      ],
      "visualCue": "Show chart with green +30%"
    },
    {
      "segmentNumber": 2,
      "duration": 25,
      "title": "Explanation",
      "voiceover": "Backtests assume perfect conditions...",
      ...
    },
    {
      "segmentNumber": 3,
      "duration": 30,
      "title": "Solution",
      "voiceover": "Here's how to fix it...",
      ...
    }
  ]
}
```

### **STEP 2: Produce Reel Video**

Use CapCut, Adobe Premiere, or similar:

1. Create 1080x1920 video (9:16 aspect ratio)
2. For each segment from Step 1:
   - Set duration to exact seconds
   - Add voiceover (AI or your own)
   - Add text overlays from response
   - Add background: trading charts, market data
3. Add music (trending, not copyrighted)
4. Export as MP4 (max 90 seconds)

**Alternative: Use AI Video Generator**
- Synthesia.io, HeyGen, or D-ID
- Upload reel script
- Generate video with avatar
- Download MP4

### **STEP 3: Upload Reel to Instagram**

#### **Manual:**
1. Instagram mobile app → "+"
2. Select "Reel"
3. Upload your MP4 video
4. Trim to 60 seconds if needed
5. Add caption + hashtags
6. Post

#### **API:**
```bash
curl -X PUT "http://localhost:3000/api/social/instagram/reel/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "videoUrl": "https://your-cdn.com/reel.mp4",
    "caption": "Mean Reversion: The Strategy Making $39K in Backtests\n\nMost traders think momentum is the answer...",
    "hashtags": ["#Trading", "#MeanReversion", ...],
    "accessToken": "YOUR_INSTAGRAM_ACCESS_TOKEN"
  }'
```

---

## PART 8: SETUP DAILY STORIES (10 minutes)

### **STEP 1: Generate Story Templates**

```bash
curl -X POST "http://localhost:3000/api/social/instagram/stories" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-06-21",
    "count": 3
  }'
```

Response:
```json
{
  "stories": [
    {
      "storyNumber": 1,
      "time": "9:00 AM ET",
      "type": "market_update",
      "content": "NVDA breaking $140 | Momentum setup active",
      "design": "Text overlay on dark background"
    },
    {
      "storyNumber": 2,
      "time": "12:00 PM ET",
      "type": "poll",
      "question": "Will market close green today?",
      "options": ["Yes", "No"]
    },
    {
      "storyNumber": 3,
      "time": "7:00 PM ET",
      "type": "engagement",
      "question": "What's your biggest trading mistake?"
    }
  ]
}
```

### **STEP 2: Create Stories**

1. Instagram mobile app → "Your Story"
2. For Market Update:
   - Text: "NVDA $140 | Momentum"
   - Background: Dark with chart
3. For Poll:
   - Use sticker → Poll
   - Question: "Will market close green?"
   - Options: Yes / No
4. For Engagement:
   - Use sticker → Question
   - Ask: "What's your biggest mistake?"

### **STEP 3: Schedule or Post**

- **Manual**: Post immediately to Stories
- **Scheduled**: Use Instagram Creator Studio to schedule all 3 stories at times above

---

## PART 9: VERIFY EVERYTHING WORKS (15 minutes)

### **STEP 1: Check Profile**

Visit your Instagram profile on mobile:
- ✅ Bio updated with trading focus
- ✅ Website link goes to free trial page
- ✅ Profile picture is professional
- ✅ First carousel post visible
- ✅ First reel visible

### **STEP 2: Check Analytics**

1. Go to Instagram Insights (top right menu)
2. Click "Posts" tab
3. Check your carousel post:
   - Views: Should be 50+ (even if new account)
   - Engagement: Likes, comments, saves
   - Reach: Total accounts reached
   - Impressions: Total displays

4. Click "Reels" tab
5. Check your reel:
   - Views: Usually higher than carousel
   - Engagement rate: Should be 8-12%
   - Saves: % of viewers who saved

### **STEP 3: Test API Endpoints**

```bash
# Test carousel endpoint
curl -X POST "http://localhost:3000/api/social/instagram/carousel" \
  -H "Content-Type: application/json" \
  -d '{"threadText": "Test", "strategy": "Test"}'

# Test reel endpoint
curl -X POST "http://localhost:3000/api/social/instagram/reel" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test", "duration": 60, "tone": "educational"}'

# Should get 200 OK responses with data
```

### **STEP 4: Verify GitHub Secrets Work**

Run test workflow:
1. Go to repo → Actions
2. Look for "Instagram" workflow
3. Click "Run workflow"
4. Check logs for:
   - ✅ Secrets loaded
   - ✅ API connected
   - ✅ Account verified

---

## PART 10: SETUP AUTOMATION FOR POSTING (30 minutes)

### **STEP 1: Connect Email Platform (for drip campaign)**

Choose ONE:

**Option A: Substack (Free)**
1. Go to https://substack.com
2. Create publication "ProfitEngine Trading"
3. Connect to email list
4. Use free tier for email automation

**Option B: Klaviyo (Recommended)**
1. Go to https://www.klaviyo.com
2. Sign up free account
3. Add your email list
4. Create automation: Carousel post → Email to followers

**Option C: ConvertKit**
1. Go to https://convertkit.com
2. Create free account
3. Add email list
4. Setup sequence automation

### **STEP 2: Setup Posting Schedule**

Create calendar for next 4 weeks:

```
WEEK 1:
  Tue 9 AM  → Post #1: "11-Strategy System"
  Thu 2 PM  → Post #2: "Mean Reversion Winner"
  Sat 9 AM  → Post #3: "Risk Gates Explained"

WEEK 2:
  Tue 9 AM  → Post #4: "Momentum Strategy"
  Thu 2 PM  → Post #5: "Breakout Trading"
  Sat 9 AM  → Post #6: "Sentiment Analysis"

WEEK 3:
  Tue 9 AM  → Post #7: "Correlation Detection"
  Thu 2 PM  → Post #8: "Technical Patterns"
  Sat 9 AM  → Post #9: "Volatility Trading"

WEEK 4:
  Tue 9 AM  → Post #10: "Integration & Proof"
  Thu 2 PM  → Reel #1: "Mean Reversion Deep Dive"
  Sat 9 AM  → Stories (3x daily)
```

### **STEP 3: Batch Create Content**

Spend 1 hour creating all carousel slides + reels for Week 1-2:

1. Open `CONTENT_CALENDAR_MONTHLY.md`
2. Pick 6 posts for Week 1-2
3. For each post:
   - Generate carousel structure (Step 6)
   - Design 7 slides in Canva (1 hour/carousel)
   - Save all PNG files
   - Generate captions + hashtags

Result: 6 carousels ready to upload (12 total hours of design work, can batch)

---

## PART 11: MEASURE & OPTIMIZE (Ongoing)

### **WEEKLY CHECKLIST**

Every Sunday, review:

```
INSTAGRAM ANALYTICS REVIEW
═══════════════════════════

Views & Reach:
  [ ] Carousel post #1: ___ views
  [ ] Carousel post #2: ___ views
  [ ] Reel #1: ___ views
  [ ] Stories: ___ views

Engagement:
  [ ] Total likes: ___
  [ ] Total comments: ___
  [ ] Total saves: ___
  [ ] Engagement rate: ___%

Growth:
  [ ] New followers: ___
  [ ] Profile visits: ___
  [ ] Website clicks: ___
  [ ] Free trial signups: ___

TOP PERFORMER:
  [ ] Best post: ___
  [ ] Best engagement: ___%
  [ ] Why it worked: (analysis)

ACTION ITEMS:
  [ ] Post more like #___
  [ ] Drop format: ___
  [ ] Test new: ___
```

### **MONTHLY OPTIMIZATION**

By Day 30:
1. Identify top 3 posts (views + engagement)
2. Analyze what worked:
   - Topic (strategy vs. psychology vs. data)
   - Format (carousel vs. reel)
   - Caption hook
   - Hashtags
   - Posting time
3. Double down on what works
4. Discontinue what doesn't
5. Set growth targets for Month 2

---

## QUICK REFERENCE

### **Instagram Account Setup Summary**

| Step | Action | Time |
|------|--------|------|
| 1 | Choose Business Account | 10 min |
| 2 | Create/optimize profile | 10 min |
| 3 | Setup Instagram Graph API | 15 min |
| 4 | Add GitHub Secrets | 10 min |
| 5 | Test API connection | 5 min |
| 6 | Generate first carousel | 45 min |
| 7 | Generate first reel | 60 min |
| 8 | Setup daily stories | 10 min |
| 9 | Verify everything works | 15 min |
| 10 | Setup email automation | 30 min |
| **TOTAL** | | **~3 hours** |

### **First Week Posts**

Copy from `CONTENT_CALENDAR_MONTHLY.md`:

```
WEEK 1 POSTS:

Post 1 (Tue 9 AM): "The 11-Strategy System That Runs While You Sleep"
Post 2 (Thu 2 PM): "Mean Reversion: The Strategy Generating +$39K in Backtests"
Post 3 (Sat 9 AM): "The 6 Risk Gates That Prevent 95% of Losses"

STORIES (3x daily):
- 9 AM: Market update (NVDA, TSLA, BTC price)
- 12 PM: Poll ("Will market close green?")
- 7 PM: Engagement Q&A ("Biggest trading mistake?")
```

### **API Endpoints Reference**

```bash
# Generate carousel
POST /api/social/instagram/carousel
Input: threadText, strategy, backtestData
Output: 7-slide carousel structure

# Generate reel script
POST /api/social/instagram/reel
Input: topic, duration (30/60), tone
Output: Full reel script with timing

# Publish carousel
PUT /api/social/instagram/carousel/publish
Input: slides (image URLs), caption, hashtags
Output: Instagram carousel post link

# Get recommendations
POST /api/instagram/recommendations
Input: threadText, engagementMetrics
Output: Format suggestion, hook, hashtags, timing
```

---

## TROUBLESHOOTING

### **"Access token invalid" error**

**Solution:**
1. Go back to Part 3, Step 3
2. Generate new access token
3. Update GitHub Secrets
4. Test connection again

### **"Account ID not found" error**

**Solution:**
1. Verify Instagram Business Account ID (not personal ID)
2. Run: `curl "https://graph.instagram.com/me?fields=ig_user_id&access_token=YOUR_TOKEN"`
3. Copy the `ig_user_id` value
4. Update INSTAGRAM_BUSINESS_ACCOUNT_ID secret

### **"No images uploaded" after carousel post**

**Solution:**
1. Verify all 7 PNG files are uploaded to CDN
2. Check image URLs are correct (not local paths)
3. Verify image resolution (1080x1350px)
4. Try uploading manually first (Part 6, Option A)

### **Reel won't upload (>90 seconds or wrong aspect)**

**Solution:**
1. Open video in CapCut
2. Verify duration ≤ 60 seconds
3. Verify aspect ratio is 9:16 (1080x1920)
4. Re-export as MP4
5. Try uploading again

---

## NEXT STEPS

1. ✅ **Complete Part 1-5** (Setup account + API) → 45 minutes
2. ✅ **Complete Part 6-8** (Create carousel + reel + stories) → 2 hours
3. ✅ **Complete Part 9** (Verify everything) → 15 minutes
4. ✅ **Complete Part 10** (Setup automation) → 30 minutes
5. ✅ **Weekly Review** (Every Sunday using checklist)
6. ✅ **Monthly Optimization** (Drop underperformers, double down on wins)

**Total Time to Launch**: ~3 hours  
**Ongoing Time**: 2-3 hours/week (posting) + 30 min/week (analytics)

---

**You're ready. Start with Part 1 now.** 🚀
