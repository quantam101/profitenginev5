#!/bin/bash
# Setup Instagram & Threads automation for direct audience engagement
# Uses Meta Graph API for both platforms

set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "SETUP: INSTAGRAM & THREADS INTEGRATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Load environment
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

INSTAGRAM_TOKEN="${INSTAGRAM_ACCESS_TOKEN:-}"
THREADS_TOKEN="${THREADS_ACCESS_TOKEN:-}"

echo "[1] Instagram Setup Guide"
echo "─────────────────────────────────────────────────────────────────"
echo ""

cat > "INSTAGRAM_SETUP.md" << 'EOF'
# Instagram Setup Guide

## Account Setup
1. Go to: https://instagram.com
2. Create business account or convert existing
3. Go to: https://developers.facebook.com
4. Create app → Instagram Graph API
5. Get access token
6. Add to GitHub Secrets as INSTAGRAM_ACCESS_TOKEN

## Account Info Needed
- Instagram Business Account ID
- Add to GitHub Secrets as INSTAGRAM_BUSINESS_ACCOUNT_ID

## Content Strategy

### Profile Optimization
- Bio: "AI productivity systems | Save 10+ hours/week"
- Link: Your Gumroad product URL
- Profile image: Brand logo

### Content Pillars (3-week rotation)

**Week 1: AI Tools & Workflows**
- Carousel posts (5 slides): "5 AI tools that changed my workflow"
- Reel: Quick demo of AI tool in action
- Story: Behind-the-scenes of content creation

**Week 2: Results & Case Studies**
- Post: "How this team shipped 3 months faster"
- Reel: Before/after productivity metrics
- Story: Reader testimonial

**Week 3: Education & Prompts**
- Carousel: Copy-paste prompts (high engagement)
- Reel: Prompt templates for your job
- Story: Q&A sticker interactions

### Posting Schedule
- 3x per week (Tuesday, Thursday, Saturday)
- Best times: 9 AM, 12 PM, 7 PM (your timezone)
- Reels get 2-3x more engagement
- Carousel posts get 4-5x engagement

### Hashtag Strategy
Popular hashtags:
#AIProductivity #ProductivityTips #AITools #Automation #WorkflowOptimization
#AIAssistant #Efficiency #TimeManagement #TechTools #Learning

Mix: 30% popular (1M+ posts), 40% medium (100k-1M), 30% niche (10k-100k)

### Growth Targets
- Month 1: 100-200 followers
- Month 2: 300-500 followers
- Month 3: 800-1,200 followers
- Month 6: 2,000-3,000 followers
- Year 1: 5,000+ followers

### Monetization
- Direct DM for Gumroad link
- Bio link to landing page
- Affiliate links in captions (when applicable)
- Expected: $100-300/month from Instagram referrals

EOF

echo "✓ Instagram setup guide created: INSTAGRAM_SETUP.md"
echo ""

echo "[2] Threads Setup Guide"
echo "─────────────────────────────────────────────────────────────────"
echo ""

cat > "THREADS_SETUP.md" << 'EOF'
# Threads Setup Guide

## Account Setup
1. Go to: https://threads.net
2. Create account (links to Instagram)
3. Go to: https://developers.facebook.com
4. Enable Threads API
5. Get access token
6. Add to GitHub Secrets as THREADS_ACCESS_TOKEN

## Account Info Needed
- Threads User ID
- Add to GitHub Secrets as THREADS_USER_ID

## Content Strategy

### Why Threads?
- More direct & conversation-focused than Twitter
- Less algorithm manipulation
- Better for building community
- Growing audience (5M+ monthly users)
- Perfect for professional/technical audience

### Content Pillars

**Thread Type 1: Long-form insights (5-7 tweets)**
"Here's what I learned this week about AI productivity..."
- Share specific lessons
- Include actionable steps
- End with engagement question

**Thread Type 2: Quick wins**
"3 AI tools that save me 2 hours daily"
1. ChatGPT for...
2. Claude for...
3. Perplexity for...

**Thread Type 3: Prompts & templates**
"Copy-paste prompt that generates 10 content ideas in 2 minutes"
[Full prompt]
[Expected output]
[Tips for customization]

**Thread Type 4: Question & discussion**
"What's the #1 AI tool you use daily?"
- Ask for replies
- Quote their answers
- Build community

### Posting Schedule
- 1x per day (morning, 9 AM)
- Threads get better reach with consistent posting
- Quality > quantity
- Engage with others' threads (10+ interactions daily)

### Growth Strategy
- Reply to trending threads in your niche
- Quote posts from your audience
- Ask questions to drive engagement
- Share behind-the-scenes
- Provide genuine value (not selling)

### Monetization
- Build audience first
- Link to Gumroad in profile
- DM traffic → conversions
- Long-term: Sponsorships possible
- Expected: $50-200/month from Threads

### Engagement Tactics
- Reply to every comment first hour
- Like & comment on related threads
- Repost your best insights
- Create polls & questions
- Share reader stories/testimonials

### Growth Targets
- Month 1: 50-100 followers
- Month 2: 200-300 followers
- Month 3: 500-800 followers
- Month 6: 1,500-2,000 followers
- Year 1: 3,000-5,000 followers

EOF

echo "✓ Threads setup guide created: THREADS_SETUP.md"
echo ""

echo "[3] Creating automation scripts"
echo "─────────────────────────────────────────────────────────────────"
echo ""

mkdir -p "scripts/social_automation"

cat > "scripts/social_automation/instagram_poster.py" << 'EOF'
#!/usr/bin/env python3
"""
Instagram poster - uploads content via Meta Graph API
"""

import os
import requests
import json
from datetime import datetime

INSTAGRAM_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
INSTAGRAM_API_VERSION = 'v18.0'

def upload_image_post(image_url: str, caption: str, hashtags: str = ""):
    """Upload image post to Instagram"""

    endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"

    full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

    payload = {
        'image_url': image_url,
        'caption': full_caption,
        'access_token': INSTAGRAM_TOKEN
    }

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        print(f"✓ Image post created: {response.json()['id']}")
        return response.json()['id']
    else:
        print(f"✗ Error: {response.text}")
        return None

def upload_carousel(image_urls: list, caption: str, hashtags: str = ""):
    """Upload carousel post to Instagram"""

    endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"

    # Create carousel items
    carousel_items = []
    for idx, img_url in enumerate(image_urls):
        item_payload = {
            'image_url': img_url,
            'access_token': INSTAGRAM_TOKEN
        }
        response = requests.post(endpoint, json=item_payload)
        if response.status_code == 200:
            carousel_items.append(response.json()['id'])

    # Create carousel container
    container_endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"
    full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

    container_payload = {
        'media_type': 'CAROUSEL',
        'children': carousel_items,
        'caption': full_caption,
        'access_token': INSTAGRAM_TOKEN
    }

    response = requests.post(container_endpoint, json=container_payload)

    if response.status_code == 200:
        print(f"✓ Carousel post created: {response.json()['id']}")
        return response.json()['id']
    else:
        print(f"✗ Error: {response.text}")
        return None

def get_insights():
    """Get engagement metrics"""

    endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/insights"

    metrics = [
        'impressions',
        'reach',
        'follower_count',
        'website_clicks'
    ]

    params = {
        'metric': ','.join(metrics),
        'period': 'day',
        'access_token': INSTAGRAM_TOKEN
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        insights = response.json()['data']
        print("\n[Instagram Insights]")
        for metric in insights:
            print(f"  {metric['name']}: {metric.get('values', [{}])[0].get('value', 'N/A')}")
    else:
        print(f"✗ Error fetching insights: {response.text}")

if __name__ == '__main__':
    print("Instagram posting automation ready")
    print(f"Account ID: {INSTAGRAM_ACCOUNT_ID}")

    # Example usage:
    # upload_image_post(
    #     image_url="https://example.com/image.jpg",
    #     caption="Check out this AI productivity tip!",
    #     hashtags="#AIProductivity #Automation #Tips"
    # )
EOF

chmod +x "scripts/social_automation/instagram_poster.py"
echo "✓ Instagram poster script created"
echo ""

cat > "scripts/social_automation/threads_poster.py" << 'EOF'
#!/usr/bin/env python3
"""
Threads poster - posts directly to Threads via Meta Graph API
More direct engagement with minimal algorithm interference
"""

import os
import requests
import json
from datetime import datetime

THREADS_TOKEN = os.getenv('THREADS_ACCESS_TOKEN')
THREADS_USER_ID = os.getenv('THREADS_USER_ID')
THREADS_API_VERSION = 'v18.0'

def post_thread(text: str, image_url: str = None):
    """Post to Threads"""

    endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{THREADS_USER_ID}/threads"

    payload = {
        'text': text,
        'access_token': THREADS_TOKEN
    }

    if image_url:
        payload['image_url'] = image_url

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        thread_id = response.json()['id']
        print(f"✓ Thread posted: {thread_id}")

        # Publish the thread
        publish_endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{thread_id}/publish"
        publish_response = requests.post(publish_endpoint, json={'access_token': THREADS_TOKEN})

        if publish_response.status_code == 200:
            print(f"✓ Thread published!")
            return thread_id

    print(f"✗ Error: {response.text}")
    return None

def reply_to_thread(thread_id: str, text: str):
    """Reply to a thread"""

    endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{thread_id}/replies"

    payload = {
        'text': text,
        'access_token': THREADS_TOKEN
    }

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        print(f"✓ Reply posted")
        return response.json()['id']

    print(f"✗ Error: {response.text}")
    return None

def get_thread_insights(thread_id: str):
    """Get thread engagement metrics"""

    endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{thread_id}/insights"

    params = {
        'metric': 'likes,replies,reposts,quotes',
        'access_token': THREADS_TOKEN
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        insights = response.json()['data']
        print(f"\n[Thread {thread_id} Insights]")
        for metric in insights:
            print(f"  {metric['title']}: {metric['values'][0]['value']}")
    else:
        print(f"✗ Error: {response.text}")

if __name__ == '__main__':
    print("Threads posting automation ready")
    print(f"User ID: {THREADS_USER_ID}")

    # Example usage:
    # post_thread("Here's my latest AI productivity insight...")
EOF

chmod +x "scripts/social_automation/threads_poster.py"
echo "✓ Threads poster script created"
echo ""

echo "[4] Creating GitHub Secrets checklist"
echo "─────────────────────────────────────────────────────────────────"
echo ""

cat > ".github/INSTAGRAM_THREADS_SECRETS.md" << 'EOF'
# Instagram & Threads Secrets Setup

## Required Secrets

### Instagram
```
INSTAGRAM_ACCESS_TOKEN
  Get from: https://developers.facebook.com → Instagram Graph API
  Format: Starts with IGQVJ...
  Scope needed: instagram_business_content_publish
```

```
INSTAGRAM_BUSINESS_ACCOUNT_ID
  Get from: Meta Business Suite → Instagram Account Settings
  Format: Numeric ID (18+ digits)
```

### Threads
```
THREADS_ACCESS_TOKEN
  Get from: https://developers.facebook.com → Threads API
  Format: Starts with IGQVJ... (same token as Instagram)
  Scope needed: threads_publish
```

```
THREADS_USER_ID
  Get from: Threads account settings
  Format: Numeric ID
```

## Setup Steps

### 1. Create Meta App
1. Go to: https://developers.facebook.com
2. Click "Create App"
3. Choose "Consumer" app type
4. Fill in app details
5. Add Instagram Graph API & Threads API products

### 2. Connect Instagram Business Account
1. In app settings, go to Instagram Graph API
2. Add test users or connect business account
3. Get Instagram Business Account ID
4. Generate long-lived access token (60 days)

### 3. Enable Threads API
1. In app settings, go to Threads
2. Enable Threads API
3. Request necessary permissions
4. Get Threads access token

### 4. Add to GitHub Secrets
1. Go to repo Settings → Secrets
2. Add each secret from above
3. Save

## Testing

```bash
# Test Instagram token
curl -H "Authorization: Bearer $INSTAGRAM_ACCESS_TOKEN" \
  https://graph.instagram.com/me

# Test Threads token
curl -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  https://graph.threads.net/me
```

Both should return user info.

EOF

echo "✓ Secrets checklist created"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✓ INSTAGRAM & THREADS SETUP COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "NEXT STEPS:"
echo ""
echo "1. Setup Instagram:"
echo "   - Create/convert business account"
echo "   - Follow: INSTAGRAM_SETUP.md"
echo "   - Add secrets: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID"
echo ""
echo "2. Setup Threads:"
echo "   - Create account (links to Instagram)"
echo "   - Follow: THREADS_SETUP.md"
echo "   - Add secrets: THREADS_ACCESS_TOKEN, THREADS_USER_ID"
echo ""
echo "3. Create automation:"
echo "   - Use: scripts/social_automation/instagram_poster.py"
echo "   - Use: scripts/social_automation/threads_poster.py"
echo ""
echo "4. Start posting:"
echo "   - 3x/week on Instagram (Reels + Carousels)"
echo "   - 1x/day on Threads (Long-form insights)"
echo ""

echo "EXPECTED RESULTS:"
echo "  Instagram: 100-300 followers month 1 → \$100-300/month revenue"
echo "  Threads: 50-150 followers month 1 → \$50-200/month revenue"
echo "  Combined: \$150-500/month from direct engagement"
echo ""

echo "Total social channels now: 5"
echo "  ✓ Gumroad (direct sales)"
echo "  ✓ ProductHunt (launch traffic)"
echo "  ✓ Instagram (visual content)"
echo "  ✓ Threads (direct conversation)"
echo "  ✓ Twitter/Reddit/LinkedIn (existing)"
echo ""
