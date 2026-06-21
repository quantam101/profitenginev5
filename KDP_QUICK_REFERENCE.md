# KDP Automation — Quick Reference Card

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Set environment variables
export KDP_ACCESS_TOKEN="your-token"
export OPENAI_API_KEY="sk-..."
export IMAGE_GENERATION_API="dalle"

# 2. Create a book
cat > KDP_BOOK_mybook.md << 'EOF'
---
title: My Book Title
author: Your Name
description: Short description
category: Business
price: 9.99
keywords: [business, marketing]
---

# Chapter 1
Your content here...
EOF

# 3. Publish via API
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Content-Type: application/json" \
  -d '{"operation": "publish"}'

# 4. Check results
ls -la .runtime/kdp/
```

---

## 📁 Key Files

| File | Purpose | Size |
|------|---------|------|
| `app/lib/automation/kdp.ts` | Core library | 25 KB |
| `app/api/automation/kdp/route.ts` | REST API | 7 KB |
| `KDP_AUTOMATION_GUIDE.md` | User guide | 14 KB |
| `KDP_AUTOMATION_EXAMPLES.md` | Code examples | 16 KB |

---

## 🔌 API Endpoints

### Publish Books
```bash
POST /api/automation/kdp
Content-Type: application/json

{
  "operation": "publish",
  "platforms": ["kdp", "draft2digital", "smashwords"]
}
```

### Track Royalties
```bash
GET /api/automation/kdp?asin=B0A1B2C3D4E5F6G7
```

### Get Status
```bash
GET /api/automation/kdp
```

---

## 📋 Book Metadata (Required Fields)

```yaml
title: Book Title (max 100 chars)
author: Author Name
description: Short description (max 200 chars)
category: Business | Fiction | etc.
price: 9.99 (must be $2.99-$999.99)
keywords: [keyword1, keyword2]  # max 7
```

## Optional Metadata

```yaml
subtitle: Optional subtitle
isbn: 978-1234567890
language: en | es | fr
copyright_year: 2024
publisher: Your Company
series: Series Name,1
cover_image_prompt: Custom cover description
```

---

## 🖼️ Cover Generation Providers

| Provider | Quality | Speed | Cost |
|----------|---------|-------|------|
| DALL-E | Excellent | 10-30s | $0.02 |
| Unsplash | Good | 2-5s | Free |
| Pexels | Good | 2-5s | Free |
| Replicate | Good | 20-60s | $0.001-0.01 |

---

## 🌍 Platform Comparison

| Feature | KDP | Draft2Digital | Smashwords |
|---------|-----|---------------|-----------|
| Royalty Rate | 35% | 40% | 35% |
| Publishing Time | 12-48h | 24-48h | 3-5 days |
| Distribution | Amazon only | 15+ retailers | Global |
| Min Price | $2.99 | None | None |

---

## 🔑 Environment Variables

```env
# Required
KDP_ACCESS_TOKEN=your-token
DRAFT2DIGITAL_API_KEY=your-key
SMASHWORDS_API_KEY=your-key

# Pick one image provider
IMAGE_GENERATION_API=dalle
OPENAI_API_KEY=sk-...
# OR
UNSPLASH_API_KEY=...
# OR
PEXELS_API_KEY=...
# OR
REPLICATE_API_TOKEN=...

# Optional
AUTOMATION_API_TOKEN=your-secret
```

---

## 🎯 Typical Workflow

```
1. Create KDP_BOOK_*.md file
          ↓
2. Set environment variables
          ↓
3. POST /api/automation/kdp
          ↓
4. System finds books → Generates covers → Publishes
          ↓
5. Check .runtime/kdp/ for results
          ↓
6. Verify on KDP/D2D/Smashwords dashboards (1-5 days)
          ↓
7. Track sales & earnings via dashboards
```

---

## 💰 Revenue Per Sale

**Average across 3 platforms:**
- $9.99 book × ~35% average = **~$3.50 per sale**
- Across all 3: **~$11-12 total per sale**
- Break-even: 1 sale (covers $0.02 cover cost)

---

## 📊 Results Format

**Location:** `.runtime/kdp/`

```json
{
  "metadata": { "title": "...", "author": "..." },
  "uploads": [
    {
      "platform": "kdp",
      "success": true,
      "asin": "B0A1B2C3D4E5F6G7",
      "royaltyRate": 0.35
    },
    { "platform": "draft2digital", "success": true },
    { "platform": "smashwords", "success": true }
  ],
  "overallSuccess": true
}
```

---

## ⚡ Common Commands

```bash
# View results
cat .runtime/kdp/publication-summary_*.json | jq '.'

# Check specific book
cat .runtime/kdp/*.json | jq '.metadata.title'

# View uploads only
cat .runtime/kdp/*.json | jq '.uploads[] | {platform, success, asin}'

# Count successes
cat .runtime/kdp/*.json | jq '[.uploads[] | select(.success)] | length'

# Track royalties
curl "http://localhost:3000/api/automation/kdp?asin=B0A1B2C3D4E5F6G7"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "API token not configured" | Check `.env.local` or GitHub Secrets |
| "Cover generation failed" | Verify API key, check quota |
| "Publication failed" | Check price ($2.99-$999.99), metadata valid |
| "ASIN not found" | Book must be published 12-48h, must have 1 sale |
| "Connection timeout" | Check API rate limits, retry after 60s |

---

## 📖 Documentation Files

- **Quick reference:** This file
- **Complete guide:** `KDP_AUTOMATION_GUIDE.md`
- **Code examples:** `KDP_AUTOMATION_EXAMPLES.md`
- **Integration:** `KDP_INTEGRATION_GUIDE.md`
- **Summary:** `KDP_AUTOMATION_SUMMARY.md`

---

## 🔄 TypeScript Usage

```typescript
import {
  parseBookMetadata,
  generateBookCover,
  orchestrateKdpPublication,
} from '@/app/lib/automation/kdp';

// Publish all books
const results = await orchestrateKdpPublication();

// Or manually:
const metadata = await parseBookMetadata('KDP_BOOK_*.md');
const cover = await generateBookCover(metadata);
const result = await uploadToKdp(metadata, cover);
```

---

## 🎨 Example Book Structure

```markdown
---
title: My Book
author: Your Name
description: What it's about
category: Business
price: 14.99
keywords: [keyword1, keyword2, keyword3]
---

# Introduction

Your intro...

## Chapter 1

### Section 1.1

Content here...

## Chapter 2

More content...

---

Appendix
```

---

## ⏱️ Timeline

- **Publish:** Instant (0-1 minute)
- **KDP indexed:** 12-48 hours
- **D2D live:** 24-48 hours
- **Smashwords live:** 3-5 days
- **First sales:** 1-2 weeks
- **First royalties:** 1-3 months
- **Full earnings potential:** 3-6 months

---

## 💡 Pro Tips

1. **Price strategically** — $9.99-$14.99 for non-fiction, $4.99-$7.99 for fiction
2. **Use all 7 keywords** — Target long-tail keywords
3. **Create a series** — Series books get 25-30% higher sales
4. **Professional covers** — $0.02 DALL-E or hire $50 designer
5. **Batch publish** — Create 5-10 books, publish together
6. **Track daily sales** — First 30 days determine rank

---

## 🚀 Next Actions

- [ ] Read `KDP_AUTOMATION_GUIDE.md` (15 min)
- [ ] Create first book file (20 min)
- [ ] Test cover generation (5 min)
- [ ] Publish to API (5 min)
- [ ] Check results (5 min)
- [ ] Create 4 more books (3 hours)
- [ ] Batch publish (30 min)
- [ ] Monitor results (ongoing)

---

## 📞 Support

**Documentation:**
- Questions about usage → See `KDP_AUTOMATION_GUIDE.md`
- Code examples → See `KDP_AUTOMATION_EXAMPLES.md`
- Integration → See `KDP_INTEGRATION_GUIDE.md`

**API:**
- Endpoint: `POST /api/automation/kdp`
- Library: Import from `app/lib/automation/kdp`

**External:**
- KDP Help: https://kdp.amazon.com/help
- D2D Help: https://www.draft2digital.com/help
- Smashwords Help: https://www.smashwords.com/faq

---

**Status:** ✅ Production Ready  
**Version:** 1.0  
**Last Updated:** June 20, 2024  

🎯 **Ready to publish your first book?** Start with the Quick Start section above!
