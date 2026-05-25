# Affiliate Revenue Setup Guide

ProfitEngine automatically injects affiliate links into every published article
via the `AFFILIATE_LINKS` env var. Once your accounts are approved, add your
referral URLs and every new article will include them naturally.

---

## Step 1 — Sign Up for Affiliate Programs

Apply to these programs first (approval takes 1–7 days each):

| Program | Category | Commission | Sign-Up URL |
|---------|----------|------------|-------------|
| **Amazon Associates** | Books, hardware, software | 1–10% | https://affiliate-program.amazon.com/ |
| **DigitalOcean** | Cloud VPS hosting | $25/referral | https://www.digitalocean.com/referral-program |
| **Hostinger** | Web hosting | Up to 60% | https://www.hostinger.com/affiliates |
| **Namecheap** | Domains + hosting | 20–35% | https://www.namecheap.com/affiliates/ |
| **Semrush** | SEO tools | $200/sale | https://www.semrush.com/affiliate/ (via Impact.com) |
| **Jasper AI** | AI writing tool | 30% recurring | https://www.jasper.ai/affiliate-program |
| **Copy.ai** | AI writing tool | 45% recurring | https://www.copy.ai/affiliates |
| **Beehiiv** | Newsletter platform | 50% recurring | https://www.beehiiv.com/partner |
| **Teachable** | Online courses | 30% recurring | https://teachable.com/affiliates |
| **ConvertKit** | Email marketing | 30% recurring | https://convertkit.com/affiliate |

---

## Step 2 — Add Your Links to the Server `.env`

Once approved, log into each affiliate dashboard, copy your unique referral URL,
and add them to `/home/ubuntu/profitenginev5/.env` on the server:

```bash
AFFILIATE_LINKS={"VPS hosting": "https://m.do.co/c/YOUR_DO_REF", "web hosting": "https://www.hostinger.com/YOUR_REF", "SEO tools": "https://www.semrush.com/YOUR_REF", "AI writing tool": "https://www.jasper.ai/YOUR_REF", "email marketing": "https://app.convertkit.com/referrals/YOUR_REF", "online courses": "https://teachable.com/YOUR_REF"}
```

The keywords (left side) are matched against `[AFFILIATE:keyword]` placeholders
that the content-gen agent inserts. Add as many or few as you like — unmatched
placeholders are automatically stripped.

---

## Step 3 — Restart the Runtime

After editing `.env`, restart the runtime container to pick up new env vars:

```bash
cd /home/ubuntu/profitenginev5
docker compose restart runtime
```

---

## How It Works

1. `content-gen` agent generates an article and inserts `[AFFILIATE:keyword]` markers
2. `blog-publisher` agent calls `_inject_affiliate_links()` which swaps markers for real URLs
3. Article is published to GitHub Pages + Dev.to with live affiliate links

### Example transformation

**Before injection:**
```markdown
For hosting your AI projects, consider [AFFILIATE:VPS hosting] which offers
generous free tiers.
```

**After injection (with DigitalOcean link):**
```markdown
For hosting your AI projects, consider [VPS hosting](https://m.do.co/c/YOUR_REF) which offers
generous free tiers.
```

---

## Realistic Revenue Projections

| Monthly Visitors | Affiliate CTR | Conv. Rate | Avg. Commission | Monthly Revenue |
|-----------------|---------------|------------|-----------------|-----------------|
| 500 | 3% | 2% | $30 | ~$9 |
| 2,000 | 3% | 2% | $30 | ~$36 |
| 10,000 | 3% | 2% | $30 | ~$180 |
| 50,000 | 3% | 2% | $30 | ~$900 |

Traffic grows as Google indexes more articles. ProfitEngine publishes one article/day
automatically (via the n8n daily cron at 07:00 UTC), so the library compounds over time.

---

## Pro Tips

- **Amazon Associates**: Great for recommending specific books (e.g. "Python for Data Science").
  Add ISBNs as keywords: `"Python for Data Science book": "https://amzn.to/YOUR_ASIN"`

- **DigitalOcean**: Especially relevant for the "VPS hosting" and "cloud hosting" keywords
  the content-gen agent naturally inserts in tech articles.

- **Recurring commissions** (Jasper, ConvertKit, Beehiiv) compound monthly. Prioritize these.

- **Disclosure**: Add `<!-- affiliate disclosure -->` to your Jekyll `_layouts/post.html`
  to stay FTC-compliant. Required by law in the US.
