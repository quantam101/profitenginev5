# Tips Curator Integration Guide

**How to integrate Tips Curator into ProfitEngine's content distribution pipeline.**

---

## Architecture Overview

```
Published Articles (GitHub)
    ↓
    [Tips Curator] — Extract 3-5 actionable tips per article
    ↓
    [Format] — Twitter/LinkedIn/Instagram/Email/Blog
    ↓
    [Monetize] — Inject affiliate links, sponsor CTAs
    ↓
    [Distribute] — Publish to all social channels
    ↓
    [Aggregate] — Collect engagement metrics
    ↓
    [Ebook] — Compile into "101 Tips" for Gumroad
```

---

## 1. GitHub Actions Automation

### Setup: Auto-Extract Tips on Article Publish

Create `.github/workflows/extract-tips.yml`:

```yaml
name: Extract Tips on Article Publish

on:
  push:
    branches: [main]
    paths:
      - 'posts/*.md'

jobs:
  extract-tips:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          repository: quantam101/already-here-llc
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install httpx python-dotenv
      
      - name: Extract tips from new article
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GITHUB_CONTENT_TOKEN: ${{ secrets.GITHUB_CONTENT_TOKEN }}
          GITHUB_CONTENT_OWNER: quantam101
          GITHUB_CONTENT_REPO: content
          AFFILIATE_LINKS: ${{ secrets.AFFILIATE_LINKS }}
          AMAZON_PARTNER_TAG: alreadyhere-20
          MONETIZATION_ENABLED: 'true'
        run: |
          python scripts/tips_curator.py \
            --extract \
            --format all \
            --ebook \
            --days 1
      
      - name: Commit tips to repo
        run: |
          git config --global user.email "github-actions@already-here-llc.com"
          git config --global user.name "Tips Curator Bot"
          git add data/tips/
          git commit -m "feat: auto-extract tips from new article" || true
          git push
      
      - name: Upload to social media
        env:
          TWITTER_API_KEY: ${{ secrets.TWITTER_API_KEY }}
          TWITTER_API_SECRET: ${{ secrets.TWITTER_API_SECRET }}
          TWITTER_ACCESS_TOKEN: ${{ secrets.TWITTER_ACCESS_TOKEN }}
          TWITTER_ACCESS_SECRET: ${{ secrets.TWITTER_ACCESS_SECRET }}
          LINKEDIN_ACCESS_TOKEN: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
          INSTAGRAM_ACCESS_TOKEN: ${{ secrets.INSTAGRAM_ACCESS_TOKEN }}
        run: |
          python scripts/publish_tips_to_socials.py
```

---

## 2. N8N Workflow Integration

### Publish Tips on Schedule

Create N8N workflow `workflows/daily-tips-publisher.json`:

```json
{
  "name": "Daily Tips Publisher",
  "nodes": [
    {
      "name": "Trigger Daily at 9 AM",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "cronExpression": "0 9 * * *",
        "timezone": "America/New_York"
      }
    },
    {
      "name": "Extract Tips",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "cd /app && python scripts/tips_curator.py --extract --generate-daily --format all"
      }
    },
    {
      "name": "Load Tips JSON",
      "type": "n8n-nodes-base.readFiles",
      "parameters": {
        "path": "data/tips/twitter_tips_*.json"
      }
    },
    {
      "name": "Publish to Twitter",
      "type": "n8n-nodes-base.twitter",
      "parameters": {
        "operation": "post",
        "text": "{{ $node['Load Tips JSON'].json.body }}"
      }
    },
    {
      "name": "Publish to LinkedIn",
      "type": "n8n-nodes-base.linkedin",
      "parameters": {
        "operation": "post",
        "text": "{{ $node['Load Tips JSON'].json.body }}"
      }
    },
    {
      "name": "Send Email Newsletter",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "to": "{{ $node['Merge List'].json.emails }}",
        "subject": "Daily Tip from Already Here LLC",
        "htmlBody": "{{ $node['Load Tips JSON'].json.body }}"
      }
    }
  ]
}
```

---

## 3. Dashboard Integration

### Update Admin Control Panel

Add to `dashboard/components/TipsSection.tsx`:

```tsx
import { useEffect, useState } from 'react';

export function TipsSection() {
  const [tips, setTips] = useState([]);
  const [ebook, setEbook] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    loadTipsData();
  }, []);

  const loadTipsData = async () => {
    try {
      // Fetch tips manifest
      const manifest = await fetch('/data/tips/manifest.json').then(r => r.json());
      setTips(manifest);

      // Fetch ebook metadata
      const ebookData = await fetch('/data/tips/ebook_draft.json').then(r => r.json());
      setEbook(ebookData);

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load tips:', error);
    }
  };

  const runExtraction = async () => {
    try {
      const response = await fetch('/api/admin/tips/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 7 })
      });
      
      if (response.ok) {
        await loadTipsData();
        alert('Tips extracted successfully!');
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <div className="tips-section">
      <h2>Tips Curator Dashboard</h2>
      
      <button onClick={runExtraction}>
        Extract Tips Now
      </button>

      <div className="stats">
        <div>Total Tips: {tips.twitter?.length || 0}</div>
        <div>Ebook Chapters: {ebook?.chapters?.length || 0}</div>
        <div>Last Updated: {lastUpdated?.toLocaleString()}</div>
      </div>

      <div className="channels">
        {Object.entries(tips).map(([channel, tips_list]) => (
          <div key={channel} className="channel">
            <h3>{channel}</h3>
            <p>{tips_list.length} tips formatted</p>
          </div>
        ))}
      </div>

      <div className="ebook">
        <h3>101 Tips Ebook</h3>
        {ebook && (
          <>
            <p>Chapters: {ebook.chapters.length}</p>
            <p>Total Tips: {ebook.total_tips}</p>
            <a href={`/data/tips/ebook_draft.md`} download>
              Download Markdown
            </a>
          </>
        )}
      </div>
    </div>
  );
}
```

Add API endpoint to `backend/api/admin/tips.go`:

```go
// POST /api/admin/tips/extract
func HandleTipsExtraction(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }

    var req struct {
        Days int `json:"days"`
    }
    
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Bad request", http.StatusBadRequest)
        return
    }

    if req.Days == 0 {
        req.Days = 7
    }

    // Run tips curator script
    cmd := exec.Command(
        "python",
        "scripts/tips_curator.py",
        "--extract",
        "--format", "all",
        "--ebook",
        "--days", strconv.Itoa(req.Days),
    )
    
    if err := cmd.Run(); err != nil {
        http.Error(w, fmt.Sprintf("Failed to extract tips: %v", err), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{
        "status": "success",
        "message": "Tips extracted successfully",
    })
}
```

---

## 4. Email Distribution Integration

### Update Newsletter Publisher

Modify `scripts/newsletter_publisher.py`:

```python
import json
from pathlib import Path
from tips_curator import FormattedTip

def add_daily_tip_section(newsletter_content: str) -> str:
    """Inject latest formatted tip into newsletter."""
    tips_dir = Path("data/tips")
    
    # Load latest email-formatted tips
    email_tips_files = sorted(tips_dir.glob("email_tips_*.json"), reverse=True)
    if not email_tips_files:
        return newsletter_content
    
    with open(email_tips_files[0]) as f:
        tips = json.load(f)
    
    if tips:
        tip = tips[0]  # Most recent
        tip_section = f"""
        <h3>💡 Tip of the Day</h3>
        <p>{tip['headline']}</p>
        <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #007bff;">
          {tip['body']}
        </div>
        <p><a href="#">{tip['cta']}</a></p>
        """
        
        # Insert before footer
        return newsletter_content.replace("<!-- FOOTER -->", tip_section + "<!-- FOOTER -->")
    
    return newsletter_content
```

### Add to Email List Manager

Update `scripts/email_list_manager.py`:

```python
def send_daily_tips_digest(emails: List[str]) -> int:
    """Send digest of day's tips to subscribers."""
    tips_dir = Path("data/tips")
    
    # Load all formatted tips from today
    email_tips = load_todays_tips(tips_dir / "email_tips_*.json")
    
    if not email_tips:
        print("[SKIP] No tips found for today")
        return 0
    
    # Build email
    subject = "📧 Your Daily Tips from Already Here LLC"
    
    html_body = "<h1>Today's Tips</h1>\n"
    for tip in email_tips:
        html_body += f"""
        <div style="border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
          <h3>{tip['headline']}</h3>
          {tip['body']}
          <p><a href="#">{tip['cta']}</a></p>
        </div>
        """
    
    # Send via email service
    sent = 0
    for email in emails:
        if send_email(email, subject, html_body):
            sent += 1
    
    return sent
```

---

## 5. Gumroad Integration

### Auto-Upload Ebook

Create `scripts/publish_ebook_to_gumroad.py`:

```python
#!/usr/bin/env python3
"""Publish 101 Tips ebook to Gumroad automatically."""

import json
import os
from pathlib import Path
import httpx

GUMROAD_API_URL = "https://api.gumroad.com/v2"
GUMROAD_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN", "")
GUMROAD_PRODUCT_ID = os.getenv("GUMROAD_PRODUCT_ID", "")

async def publish_ebook_to_gumroad():
    """Upload ebook draft to Gumroad."""
    
    # Load ebook
    ebook_md = Path("data/tips/ebook_draft.md").read_text()
    ebook_json = json.loads(Path("data/tips/ebook_draft.json").read_text())
    
    # Prepare Gumroad product update
    payload = {
        "product_id": GUMROAD_PRODUCT_ID,
        "name": ebook_json["title"],
        "description": ebook_json["subtitle"],
        "price": "999",  # cents = $9.99
        "content": ebook_md,
        "tags": ["tips", "productivity", "business"],
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GUMROAD_API_URL}/products",
            headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"},
            json=payload,
        )
        
        if response.status_code == 200:
            print(f"[SUCCESS] Ebook published to Gumroad")
            return response.json()
        else:
            print(f"[ERROR] Failed to publish ebook: {response.text}")
            return None

if __name__ == "__main__":
    asyncio.run(publish_ebook_to_gumroad())
```

Run in GitHub Actions:

```yaml
- name: Publish ebook to Gumroad
  if: success()
  env:
    GUMROAD_ACCESS_TOKEN: ${{ secrets.GUMROAD_ACCESS_TOKEN }}
    GUMROAD_PRODUCT_ID: ${{ secrets.GUMROAD_PRODUCT_ID }}
  run: python scripts/publish_ebook_to_gumroad.py
```

---

## 6. Content Recycling Loop

### Complete Content Journey

```
1. Author writes article → GitHub repo (quantam101/content)
↓
2. GitHub Actions triggers → Article published to GitHub Pages
↓
3. Tips Curator runs → Extracts 3-5 tips per article
↓
4. Format workflow → 5 channel-specific versions
↓
5. Social distribution → Twitter, LinkedIn, Instagram (async)
↓
6. Email newsletter → Tip inserted into daily digest
↓
7. Blog homepage → "Daily Tip" section updated
↓
8. Engagement tracking → Metrics collected per tip
↓
9. Ebook compilation → Tips aggregated into "101 Tips"
↓
10. Gumroad sales → Monetization via product sales
↓
11. Analytics → Performance metrics fed back to dashboard
```

---

## 7. Monitoring & Analytics

### Track Tip Performance

Create `scripts/track_tip_metrics.py`:

```python
#!/usr/bin/env python3
"""Track performance of published tips across channels."""

import json
from pathlib import Path
from datetime import datetime, timedelta

class TipAnalytics:
    def __init__(self):
        self.metrics_file = Path("data/tips/metrics.json")
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        if self.metrics_file.exists():
            return json.loads(self.metrics_file.read_text())
        return {}
    
    def record_engagement(self, tip_id: str, channel: str, metric: str, value: int):
        """Record engagement metric for a tip."""
        if tip_id not in self.metrics:
            self.metrics[tip_id] = {}
        
        if channel not in self.metrics[tip_id]:
            self.metrics[tip_id][channel] = {}
        
        self.metrics[tip_id][channel][metric] = value
        self._save_metrics()
    
    def _save_metrics(self):
        self.metrics_file.write_text(json.dumps(self.metrics, indent=2))
    
    def get_top_tips(self, days: int = 7, limit: int = 10):
        """Get highest-performing tips."""
        # Aggregate by engagement
        ranked = []
        for tip_id, channels in self.metrics.items():
            total_engagement = sum(
                sum(m.get("impressions", 0) + m.get("clicks", 0) + m.get("shares", 0) for m in c.values())
                for c in [channels]
            )
            ranked.append((tip_id, total_engagement))
        
        return sorted(ranked, key=lambda x: x[1], reverse=True)[:limit]
```

---

## 8. Scheduling

### Cron Jobs

Add to `ops/scheduled-tasks.yaml`:

```yaml
scheduled_tasks:
  
  - name: daily-tips-extraction
    schedule: "0 8 * * *"  # 8 AM daily
    command: python scripts/tips_curator.py --extract --format all --ebook
    
  - name: daily-tips-distribution
    schedule: "0 9 * * *"  # 9 AM daily (after extraction)
    command: python scripts/publish_tips_to_socials.py
    
  - name: weekly-ebook-update
    schedule: "0 18 * * 0"  # Sunday 6 PM
    command: python scripts/publish_ebook_to_gumroad.py
    
  - name: tips-metrics-report
    schedule: "0 17 * * *"  # 5 PM daily
    command: python scripts/track_tip_metrics.py --report
```

---

## 9. Monitoring

### Health Check

Add to `scripts/agent-healthcheck.mjs`:

```javascript
export async function checkTipsCurator() {
  const tipsDir = 'data/tips';
  
  try {
    // Check last extraction time
    const manifest = await fs.readFile(`${tipsDir}/manifest.json`, 'utf8');
    const data = JSON.parse(manifest);
    
    const lastUpdate = Math.max(
      ...Object.values(data).map((tips) => 
        tips.length > 0 ? new Date(tips[0].formatted_at) : 0
      )
    );
    
    const hoursAgo = (Date.now() - lastUpdate) / (1000 * 60 * 60);
    
    return {
      name: 'tips-curator',
      status: hoursAgo < 25 ? 'healthy' : 'stale',
      lastUpdated: new Date(lastUpdate),
      hoursAgo,
      tipsCount: Object.values(data).reduce((sum, tips) => sum + tips.length, 0),
    };
  } catch (error) {
    return {
      name: 'tips-curator',
      status: 'error',
      error: error.message,
    };
  }
}
```

---

## 10. Testing

### Unit Tests

Create `tests/test_tips_curator.py`:

```python
import pytest
from scripts.tips_curator import (
    Tip,
    format_tip_for_twitter,
    format_tip_for_linkedin,
    inject_monetization_context,
)

@pytest.fixture
def sample_tip():
    return Tip(
        id="test_tip_1",
        title="The 80/20 Rule",
        content="Focus on highest-leverage tasks.",
        category="business_insight",
        reading_time_seconds=20,
        source_article="https://example.com/article",
        key_takeaway="Prioritize ruthlessly.",
        curiosity_hook="This changed everything.",
    )

def test_twitter_formatting(sample_tip):
    formatted = format_tip_for_twitter(sample_tip)
    assert formatted.channel == "twitter"
    assert len(formatted.thread_posts) >= 2
    assert "#TipOfTheDay" in formatted.hashtags

def test_linkedin_formatting(sample_tip):
    formatted = format_tip_for_linkedin(sample_tip)
    assert formatted.channel == "linkedin"
    assert "Key Insight" in formatted.body
    assert "#ProductivityTips" in formatted.hashtags

def test_monetization_injection(sample_tip):
    tip_with_monetization = inject_monetization_context(sample_tip)
    # Should have Amazon Associates link for generic tips
    assert tip_with_monetization.monetization is not None

if __name__ == "__main__":
    pytest.main([__file__])
```

Run tests:

```bash
python -m pytest tests/test_tips_curator.py -v
```

---

## Deployment Checklist

- [ ] Set all required env vars in GitHub Secrets
- [ ] Create Gumroad product for "101 Tips" ebook
- [ ] Set up Twitter/LinkedIn/Instagram API credentials
- [ ] Create GitHub Actions workflow (`.github/workflows/extract-tips.yml`)
- [ ] Add Dashboard TipsSection component
- [ ] Configure N8N daily tips workflow
- [ ] Set up email newsletter integration
- [ ] Create monitoring in healthcheck
- [ ] Run initial test extraction
- [ ] Verify tips appear in all channels
- [ ] Monitor engagement metrics for 1 week
- [ ] Adjust hook/CTA language based on performance

---

## Support

Questions? See:
- [TIPS_CURATOR_README.md](TIPS_CURATOR_README.md) — Full documentation
- [tips_curator.py](tips_curator.py) — Source code
- [tips_curator.env.example](tips_curator.env.example) — Configuration template
