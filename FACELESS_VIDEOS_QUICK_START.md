# Faceless Videos — Quick Start Reference Card

## 🚀 60-Second Setup

### 1. Set 3 Essential Environment Variables
```bash
export REPLICATE_API_TOKEN=r8_your_token_from_replicate.com
export ELEVENLABS_API_KEY=sk_your_key_from_elevenlabs.io
export RUNTIME_API_URL=https://profitengine.alreadyherellc.com
```

### 2. Create Content Calendar
Create file: `CONTENT_CALENDAR_MONTHLY.md`

```markdown
### Post 1: "How to Make $25K/Month"
**Hook:** Discover the exact system...
**Main Content:**
1. The 4-stream model
2. Specific tools to automate
3. Real results
4. How to scale

**Call-to-Action:** Join my course - 50% off

**Tags:** AI, passive income, money, automation
```

### 3. Generate First Video
```bash
# Via CLI (easiest)
node scripts/faceless-videos-cli.mjs generate 1

# Or via curl
curl -X POST http://localhost:3000/api/automation/faceless-videos/generate \
  -H "Content-Type: application/json" \
  -d '{"postNumber": 1, "videoProvider": "replicate", "platforms": ["youtube", "tiktok"]}'
```

## 📋 Common Commands

```bash
# Generate single video
node scripts/faceless-videos-cli.mjs generate 1

# Batch generate 5 videos
node scripts/faceless-videos-cli.mjs batch 1 2 3 4 5

# Schedule video for tomorrow at 2 PM UTC
node scripts/faceless-videos-cli.mjs schedule 5 2024-06-21T14:00:00Z

# Process scheduled videos (run via cron daily)
node scripts/faceless-videos-cli.mjs process-scheduled

# View metrics
node scripts/faceless-videos-cli.mjs metrics

# Check system status
node scripts/faceless-videos-cli.mjs status
```

## 🎯 Use Cases

### Weekly Content Release (7 videos, each day)
```bash
node scripts/faceless-videos-cli.mjs batch 1 2 3 4 5 6 7
```
Videos auto-publish to YouTube, TikTok, Instagram each day.

### One-Time Video Generation
```bash
node scripts/faceless-videos-cli.mjs generate 1
```
Video generated and published immediately.

### Monthly Scheduling (30 videos over 30 days)
```bash
node scripts/faceless-videos-cli.mjs schedule 1 2024-07-01T10:00:00Z
node scripts/faceless-videos-cli.mjs schedule 2 2024-07-02T10:00:00Z
# ... repeat for 30 days
```
Then set up cron job to auto-process.

## 📊 API Endpoints Cheat Sheet

```bash
# Generate single video
POST /api/automation/faceless-videos/generate
{ "postNumber": 1, "videoProvider": "replicate", "platforms": ["youtube"] }

# Batch generate
POST /api/automation/faceless-videos/batch
{ "postNumbers": [1,2,3,4,5], "simultaneousGenerations": 2 }

# Schedule video
POST /api/automation/faceless-videos/schedule
{ "postNumber": 2, "scheduledTime": "2024-06-21T14:00:00Z" }

# Process scheduled (cron)
POST /api/automation/faceless-videos/process-scheduled

# Get metrics
GET /api/automation/faceless-videos/metrics

# Check status
GET /api/automation/faceless-videos/status
```

## 🔑 Environment Variables (All Required for Production)

| Variable | Where to Get | Example |
|----------|-------------|---------|
| `REPLICATE_API_TOKEN` | https://replicate.com | `r8_xxx...` |
| `ELEVENLABS_API_KEY` | https://elevenlabs.io | `sk_xxx...` |
| `ELEVENLABS_VOICE_ID` | elevenlabs.io account | `EXAVITQu4vr4xnSDxMaL` |
| `YOUTUBE_API_KEY` | Google Cloud Console | `AIz...` |
| `YOUTUBE_CHANNEL_ID` | YouTube Studio | `UCx...` |
| `TIKTOK_ACCESS_TOKEN` | TikTok Developer | `act...` |
| `INSTAGRAM_ACCESS_TOKEN` | Facebook Developer | `IG...` |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Business Account | `17841...` |
| `REDDIT_ACCESS_TOKEN` | Reddit OAuth | `xxx...` |
| `RUNTIME_API_URL` | Your domain | `https://profitengine...` |

## 💰 Cost Calculator

**Monthly cost for N videos:**

```
Total = (N × $0.08) + Voiceovers + Social APIs

Example (30 videos/month):
= 30 × $0.08 + $0.20 + $0
= $2.40 + $0.20
= $2.60/month
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Videos not generating | Check `REPLICATE_API_TOKEN` is valid |
| No voiceover | Check `ELEVENLABS_API_KEY` and rate limits |
| Scheduled videos not posting | Run `/process-scheduled` or check cron job |
| API returns 401 | Set `AUTOMATION_API_TOKEN` in `.env` |
| Logs missing | Check `.runtime/faceless-videos/` directory exists |

## 📁 File Locations

```
Core Library:     app/lib/automation/faceless-videos.ts
API Handler:      app/api/automation/faceless-videos/route.ts
CLI Tool:         scripts/faceless-videos-cli.mjs
User Guide:       app/lib/automation/FACELESS_VIDEOS_GUIDE.md
Code Examples:    app/lib/automation/faceless-videos-examples.ts
Logs:             .runtime/faceless-videos/ (auto-created)
```

## ✨ Pro Tips

1. **Start with single video** before batch operations
2. **Schedule in batches** of 5-7 videos (not 30 at once)
3. **Run cron job daily** at off-peak hours (8 AM UTC recommended)
4. **Check metrics weekly** to track success rates
5. **Monitor logs** in `.runtime/faceless-videos/` for errors
6. **Use custom scripts** for special content (not just calendar)
7. **Fallback providers** ensure videos always generate

## 🔄 Cron Job Setup (GitHub Actions)

Create `.github/workflows/process-videos.yml`:

```yaml
name: Process Faceless Videos

on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM UTC

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - name: Process scheduled videos
        run: |
          curl -X POST ${{ secrets.RUNTIME_API_URL }}/api/automation/faceless-videos/process-scheduled \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_TOKEN }}"
```

## 📞 Quick Links

- **Full Guide:** `app/lib/automation/FACELESS_VIDEOS_GUIDE.md`
- **Code Examples:** `app/lib/automation/faceless-videos-examples.ts`
- **Delivery Summary:** `FACELESS_VIDEOS_DELIVERY.md`
- **API Route:** `app/api/automation/faceless-videos/route.ts`
- **CLI Help:** `node scripts/faceless-videos-cli.mjs help`

## 🎓 Learn More

- Replicate docs: https://replicate.com/docs
- Eleven Labs docs: https://elevenlabs.io/docs
- Next.js API routes: https://nextjs.org/docs/app/building-your-application/routing/route-handlers

---

**Everything you need to start is above. Full details in FACELESS_VIDEOS_GUIDE.md**
