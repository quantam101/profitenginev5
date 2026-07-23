# Hybrid Video Generation: OCI Server Setup

This guide sets up video generation on your OCI Always Free server (129.146.236.177).

---

## Architecture

```
GitHub Actions (Light):
  ✅ Generate article (Groq)
  ✅ Commit to GitHub Pages
  ✅ Done

OCI Server (Heavy):
  ✅ Every 10 minutes: Check for new articles
  ✅ Generate video (FFmpeg slideshow)
  ✅ Post to 7 platforms
  ✅ Clean up
```

---

## Installation (One-time Setup)

### 1. SSH into OCI Server

```bash
ssh ubuntu@129.146.236.177
```

### 2. Clone/Update Repo

```bash
cd /home/ubuntu
git clone https://github.com/quantam101/profitenginev5.git
cd profitenginev5
git pull origin main
```

### 3. Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install httpx pillow
```

### 4. Set Environment Variables

Create `.env` file with your credentials:

```bash
cat > /home/ubuntu/profitenginev5/.env << 'EOF'
# Video generation
EAOS_VIDEO_ROOT=/home/ubuntu/profitenginev5/datacenter/video_pipeline
EAOS_GPU_ENABLED=false

# Social media credentials (fill in via each platform's developer dashboard)
TIKTOK_ACCESS_TOKEN=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=

TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=

LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=

IG_USER_ID=1077849398753613
IG_PAGE_ACCESS_TOKEN=

FB_PAGE_ID=61590010037059
FB_PAGE_ACCESS_TOKEN=

YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Article info
CANONICAL_URL=https://www.alreadyherellc.com/content/
ARTICLE_TOPIC=Best AI Tools for Passive Income in 2026
EOF

chmod 600 /home/ubuntu/profitenginev5/.env
```

### 5. Create Run Script

```bash
cat > /home/ubuntu/profitenginev5/run_video_generation.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/profitenginev5
source venv/bin/activate
source .env

# Run video generation
python3 scripts/oci_generate_and_post.py

# Log timestamp
echo "[$(date -u)] Video generation completed" >> /home/ubuntu/video_generation.log
EOF

chmod +x /home/ubuntu/profitenginev5/run_video_generation.sh
```

---

## Schedule Cron Job

### Run every 10 minutes (after articles publish at 07:05 UTC)

```bash
crontab -e
```

Add this line:

```cron
# Run video generation every 10 minutes
*/10 * * * * /home/ubuntu/profitenginev5/run_video_generation.sh >> /home/ubuntu/video_generation.log 2>&1
```

Or for specific times (e.g., 07:15, 07:25, 07:35 UTC):

```cron
# Run at 15, 25, 35, 45, 55 minutes past each hour
15,25,35,45,55 * * * * /home/ubuntu/profitenginev5/run_video_generation.sh >> /home/ubuntu/video_generation.log 2>&1

# Or just twice daily after article generation (07:15 and 19:15 UTC)
15 7,19 * * * /home/ubuntu/profitenginev5/run_video_generation.sh >> /home/ubuntu/video_generation.log 2>&1
```

Save and exit (Ctrl+X, Y, Enter in nano).

### Verify cron is set

```bash
crontab -l
```

---

## Manual Testing

### Test video generation

```bash
cd /home/ubuntu/profitenginev5
source venv/bin/activate
source .env
python3 scripts/oci_generate_and_post.py
```

Expected output:

```
[OCI Video] Starting video generation for: Best AI Tools...
[OCI Video] ✅ Video ready: ./datacenter/video_pipeline/distribution_masters/article.mp4
[OCI Video] ✅ Posted to TikTok
[OCI Video] ✅ Posted to Twitter
[OCI Video] ✅ Posted to YouTube
[OCI Video] ✅ Posted to LinkedIn
[OCI Video] ✅ Posted to Instagram
[OCI Video] ✅ Posted to Facebook
[OCI Video] ✅ Posted to Telegram
```

### View logs

```bash
tail -f /home/ubuntu/video_generation.log
```

---

## How It Works

### Daily Flow

```
07:05 UTC: GitHub Actions publishes article
           ↓
10 minutes later: OCI cron job triggers
           ↓
OCI: Fetches latest article
     Generates video (FFmpeg)
     Auto-posts to 7 platforms
           ↓
Videos live on all platforms
```

### Advantages

✅ **GitHub Actions stays light** (just articles, ~20s)
✅ **OCI handles video generation** (isolated, no GitHub limits)
✅ **Fully autonomous** (no manual steps)
✅ **Free** (uses Always Free tier)
✅ **Reliable** (cron job retries if one run fails)

### Resource Usage

- **GitHub Actions:** ~20 seconds per day
- **OCI server:** ~30-60 seconds every 10 minutes (minimal on free tier)
- **Storage:** ~50MB per day (videos retained 7 days)

---

## Troubleshooting

### Videos not generating

1. Check logs:
   ```bash
   tail -f /home/ubuntu/video_generation.log
   ```

2. Check cron is running:
   ```bash
   ps aux | grep python3
   ```

3. Test manually:
   ```bash
   /home/ubuntu/profitenginev5/run_video_generation.sh
   ```

### Platform posting fails

1. Check credentials in `.env`
2. Verify tokens are current (some expire)
3. Check social_engine logs for specific platform errors

### OCI server memory issues

The FFmpeg slideshow approach is lightweight (~500MB-1GB), but if you have issues:

1. Reduce video resolution: Edit `oci_generate_and_post.py`, change `1080x1920` to `720x1280`
2. Reduce cron frequency: Run every 30 minutes instead of 10
3. Kill old processes: `pkill -f oci_generate_and_post.py`

---

## Next Steps

1. ✅ Copy `scripts/oci_generate_and_post.py` to OCI
2. ✅ SSH into OCI and follow Installation steps above
3. ✅ Set up cron job
4. ✅ Test with `run_video_generation.sh`
5. ✅ Verify videos post to all platforms
6. ✅ Monitor logs for 24 hours

---

## Commands Quick Reference

```bash
# SSH to OCI
ssh ubuntu@129.146.236.177

# Navigate to repo
cd /home/ubuntu/profitenginev5

# Activate environment
source venv/bin/activate
source .env

# Test video generation
python3 scripts/oci_generate_and_post.py

# View logs
tail -f /home/ubuntu/video_generation.log

# Check cron jobs
crontab -l

# Edit cron
crontab -e
```

---

Once this is set up, your system is fully hybrid:
- **GitHub Actions:** Articles only (light, fast)
- **OCI Server:** Videos + posting (isolated, reliable)
- **Result:** Fully autonomous, zero manual work
