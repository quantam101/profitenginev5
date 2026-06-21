# KDP Automation System — Complete Guide

## Overview

ProfitEngine's KDP automation system publishes eBooks to multiple platforms simultaneously:
- **Amazon KDP** — largest ebook market, 35% royalty rate
- **Draft2Digital** — 40% royalty rate, distribution to Apple Books, Kobo, B&N
- **Smashwords** — 35% royalty rate, global distribution

## Quick Start

### 1. Environment Variables

Add these to your `.env.local` or GitHub Secrets:

```env
# KDP API Credentials (required for KDP)
KDP_ACCESS_TOKEN=your-kdp-api-token

# Draft2Digital Credentials (optional)
DRAFT2DIGITAL_API_KEY=your-draft2digital-api-key

# Smashwords Credentials (optional)
SMASHWORDS_API_KEY=your-smashwords-api-key

# Cover Image Generation (pick one)
IMAGE_GENERATION_API=dalle  # 'dalle' | 'unsplash' | 'pexels' | 'replicate'
OPENAI_API_KEY=sk-...       # if using DALL-E
UNSPLASH_API_KEY=...         # if using Unsplash
PEXELS_API_KEY=...           # if using Pexels
REPLICATE_API_TOKEN=...      # if using Replicate/Stable Diffusion

# Automation Token (optional, for API security)
AUTOMATION_API_TOKEN=your-secret-token
```

### 2. Create Book File

Create a file named `KDP_BOOK_*.md` in your project root:

```markdown
---
title: The Ultimate Guide to Financial Independence
subtitle: Build Wealth in 30 Days
author: Stephen Franklin
description: A practical guide to achieving financial freedom
category: Finance & Business
price: 9.99
language: en
isbn: 978-1234567890  # optional, can be auto-generated
copyright_year: 2024
publisher: Already Here LLC
keywords: [finance, investing, wealth-building, passive-income]
cover_image_prompt: Professional business book cover with charts and graphs, luxury aesthetic, modern design
series: Already Here Money Guides,1
---

# Introduction

Your book content starts here. Use standard Markdown formatting.

## Chapter 1: The Fundamentals

Content goes here...

### Key Concepts

- Point 1
- Point 2
- Point 3

## Chapter 2: Taking Action

More content...

---

## Appendix: Resources

- Resource 1
- Resource 2
```

### 3. Trigger Publication

#### Via API

```bash
# Publish all KDP_BOOK_*.md files
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-automation-token" \
  -d '{
    "operation": "publish",
    "platforms": ["kdp", "draft2digital", "smashwords"]
  }'
```

Response:
```json
{
  "success": true,
  "runId": "kdp-publication-1718894823456",
  "operation": "publish",
  "booksProcessed": 2,
  "platformsPerBook": 3,
  "estimatedDuration": "300s",
  "status": "initiated"
}
```

#### Via Node.js

```typescript
import { orchestrateKdpPublication } from '@/app/lib/automation/kdp';

const results = await orchestrateKdpPublication();
console.log(`Published ${results.length} book(s)`);
```

### 4. Track Royalties

```bash
# Get earnings for a specific ASIN
curl "http://localhost:3000/api/automation/kdp?asin=B0A1B2C3D4E5F6G7"
```

Response:
```json
{
  "success": true,
  "asin": "B0A1B2C3D4E5F6G7",
  "earnings": [
    {
      "asin": "B0A1B2C3D4E5F6G7",
      "platform": "kdp",
      "period": "2024-06",
      "units": 150,
      "revenue": 450.00,
      "royaltyRate": 0.35,
      "royaltyEarnings": 157.50,
      "currency": "USD"
    }
  ]
}
```

## API Reference

### POST /api/automation/kdp

Publish books or track royalties.

#### Publish Books

```json
{
  "operation": "publish",
  "bookFiles": ["KDP_BOOK_guide.md", "KDP_BOOK_course.md"],
  "platforms": ["kdp", "draft2digital", "smashwords"]
}
```

**Response:**
- `success`: boolean
- `runId`: Publication run ID
- `booksProcessed`: Number of books to publish
- `platformsPerBook`: Number of platforms per book
- `estimatedDuration`: Estimated completion time
- `status`: "initiated"

#### Track Royalties

```json
{
  "operation": "track-royalties",
  "asin": "B0A1B2C3D4E5F6G7"
}
```

**Response:**
- `success`: boolean
- `asin`: Book ASIN
- `earnings`: Array of earnings by period

### GET /api/automation/kdp

Get KDP automation status or track royalties.

#### Get Status

```bash
GET /api/automation/kdp
```

#### Track Royalties

```bash
GET /api/automation/kdp?asin=B0A1B2C3D4E5F6G7
```

## Metadata Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Book title (max 100 chars) |
| `author` | string | Author name |
| `description` | string | Short description (max 200 chars, appears in store) |
| `category` | string | Book category (Finance, Fiction, etc.) |
| `price` | number | List price in USD (2.99 - 999.99) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `subtitle` | string | Book subtitle |
| `keywords` | array | Search keywords (max 7, 50 chars each) |
| `isbn` | string | ISBN-13 (auto-generated if not provided) |
| `language` | string | Language code (en, es, fr, etc.) |
| `copyright_year` | number | Copyright year |
| `publisher` | string | Publisher name |
| `series` | string | "Series Name,#number" format |
| `cover_image_prompt` | string | Custom prompt for cover generation |
| `maturity_rating` | string | G, PG, PG-13, R, X (default: G) |

## Content Formatting

### Markdown Support

All three platforms support standard Markdown:

```markdown
# Heading 1
## Heading 2
### Heading 3

**Bold text**
*Italic text*
***Bold italic***

- List item 1
- List item 2

1. Numbered item 1
2. Numbered item 2

[Link text](https://example.com)

> Blockquote text
```

### Avoid These Elements

❌ **Not supported:**
- Raw HTML tags (use Markdown instead)
- JavaScript or interactive elements
- External stylesheets
- Embedded video/audio
- Form elements

✅ **Use instead:**
- Standard Markdown formatting
- Unicode characters and emojis
- Tables (with Markdown syntax)
- Code blocks with syntax highlighting

### Best Practices

1. **Use clear hierarchy:** H1 for chapters, H2 for sections, H3 for subsections
2. **Short paragraphs:** Keep paragraphs under 5-7 sentences
3. **Whitespace:** Use blank lines between sections
4. **Lists:** Use for key points (max 5-7 items per list)
5. **Code blocks:** Use ````language` for syntax highlighting

## Cover Image Generation

### DALL-E (Recommended)

Highest quality AI-generated covers.

```env
IMAGE_GENERATION_API=dalle
OPENAI_API_KEY=sk-...
```

**Cost:** $0.020 per image (HD quality)

### Unsplash (Free)

Stock photography, no cost.

```env
IMAGE_GENERATION_API=unsplash
UNSPLASH_API_KEY=...
```

**Pros:** Free, high-quality images
**Cons:** Generic stock photos, less unique

### Pexels (Free)

Stock photography, no cost.

```env
IMAGE_GENERATION_API=pexels
PEXELS_API_KEY=...
```

### Replicate (Cheap)

Stable Diffusion or FLUX models.

```env
IMAGE_GENERATION_API=replicate
REPLICATE_API_TOKEN=...
```

**Cost:** $0.001-0.01 per image

## Platform-Specific Notes

### Amazon KDP

- **Royalty rates:**
  - 35% (list prices below $2.99 or above $200)
  - 70% (list prices $2.99-$200, Select program)
- **Territories:** US, UK, Germany, France, Spain, Italy, Netherlands, Japan, Canada, Mexico, Brazil, India, Australia
- **File format:** PDF or EPUB
- **Cover:** JPEG or PNG, 8x10 inches, 300 DPI recommended
- **Publishing time:** 12-48 hours

### Draft2Digital

- **Royalty rate:** 40%
- **Distribution:** Apple Books, Kobo, B&N, Google Play, Scribd, etc.
- **Automatic price adjustments:** Available by market
- **Publishing time:** 24-48 hours

### Smashwords

- **Royalty rate:** 35%
- **Distribution:** Smashwords store + retailers
- **Wide distribution:** Apple Books, B&N, Kobo, Scribd
- **Nuclear option:** Free-to-read setting to promote
- **Publishing time:** 3-5 days

## Royalty Tracking

### Amazon KDP

KDP reports earnings with a 30-day delay. View earnings in your KDP dashboard:

```
https://kdp.amazon.com/en_US/dashboard
```

API endpoint tracks:
- Units sold
- Revenue (after refunds)
- Royalty rate (35% or 70%)
- Estimated royalties

### Draft2Digital

Draft2Digital provides:
- Real-time sales tracking
- Royalty statements by retailer
- Monthly payouts

### Smashwords

Smashwords provides:
- Weekly sales summaries
- Retailer breakdown
- Monthly earnings reports

## Results Storage

Publication results are saved to `.runtime/kdp/`:

```
.runtime/kdp/
├── publication-summary_1718894823456.json
├── The_Ultimate_Guide_1718894823456.json
└── launch-status.jsonl
```

### Summary Format

```json
{
  "totalBooks": 2,
  "successfulPublications": 2,
  "totalPlatformUploads": 6,
  "successfulUploads": 6,
  "duration": 187432,
  "results": [...]
}
```

### Individual Book Result

```json
{
  "metadata": { /* book details */ },
  "coverImageUrl": "https://...",
  "uploads": [
    {
      "platform": "kdp",
      "success": true,
      "bookId": "...",
      "asin": "B0A1B2C3D4E5F6G7",
      "status": "live",
      "royaltyRate": 0.35
    },
    { /* draft2digital */ },
    { /* smashwords */ }
  ],
  "overallSuccess": true,
  "successCount": 3,
  "failureCount": 0,
  "duration": 45231
}
```

## Troubleshooting

### "API token not configured"

Ensure your environment variables are set in:
- `.env.local` (development)
- `.env.production` (production)
- GitHub Secrets (CI/CD)

### "Cover generation failed"

Check:
1. Image API key is valid
2. API quota not exceeded
3. Prompt is descriptive (20+ characters)

### "Publication failed for platform X"

Reasons:
- **Title too long** (> 100 chars for KDP)
- **Price out of range** (< $2.99 or > $999.99 for KDP)
- **ISBN already used** (check ISBN format)
- **Keywords too many** (max 7 for KDP)
- **API rate limit** (retry after 60 seconds)

### "ASIN not found in royalty tracking"

1. Book must be live on KDP (published and indexed)
2. Book must have sold at least 1 copy
3. ASIN must be valid format (10 characters)

## Advanced Usage

### Custom Royalty Tracking

Track royalties from all platforms:

```typescript
import { trackKdpRoyalties } from '@/app/lib/automation/kdp';

async function trackAllRoyalties() {
  const asins = ['B0A1B2C3D4E5F6G7', 'B0A1B2C3D4E5F6G8'];
  
  for (const asin of asins) {
    const earnings = await trackKdpRoyalties(asin);
    console.log(`${asin}: $${earnings.reduce((sum, e) => sum + e.royaltyEarnings, 0)}`);
  }
}
```

### Batch Publishing

Publish multiple books with different settings:

```typescript
import { parseBookMetadata, generateBookCover, uploadToKdp } from '@/app/lib/automation/kdp';

async function publishBatch(fileNames: string[]) {
  for (const fileName of fileNames) {
    const metadata = await parseBookMetadata(fileName);
    const cover = await generateBookCover(metadata);
    const result = await uploadToKdp(metadata, cover);
    console.log(`${metadata.title}: ${result.success ? 'Published' : 'Failed'}`);
  }
}
```

### Metadata Validation

```typescript
import { parseBookMetadata } from '@/app/lib/automation/kdp';

async function validateBook(fileName: string) {
  const meta = await parseBookMetadata(fileName);
  
  const errors: string[] = [];
  if (meta.title.length > 100) errors.push('Title too long');
  if (meta.price < 2.99 || meta.price > 999.99) errors.push('Price out of range');
  if (meta.keywords.length > 7) errors.push('Too many keywords');
  
  return { valid: errors.length === 0, errors };
}
```

## Best Practices

### Content Strategy

1. **Price your ebook:** $2.99-$9.99 for fiction, $4.99-$19.99 for non-fiction
2. **Use series:** Books in a series get 25-30% higher sales
3. **Categories matter:** Pick the most specific category
4. **Keywords:** Use all 7, target long-tail keywords
5. **Cover:** Invest in professional cover (~$50 or DALL-E $0.02)

### Publishing Workflow

1. **Write and proofread** the manuscript
2. **Format with Markdown** following guides above
3. **Create book file** `KDP_BOOK_title.md`
4. **Generate cover** via API or custom
5. **Test metadata** with validation
6. **Publish to all platforms** simultaneously
7. **Track sales** daily in first week
8. **Adjust price** based on performance

### Royalty Maximization

- **KDP Select:** Exclusive publishing, 70% royalty, but loses draft2digital/smashwords
- **Wide distribution:** Publish everywhere, 35-40% royalty
- **Bundle discounts:** Discount subsequent books to drive series sales
- **Price testing:** Start at $4.99, adjust based on sales velocity

## Support & Monitoring

### API Health Check

```bash
curl http://localhost:3000/api/automation/kdp
```

### View Publication Logs

```bash
cat .runtime/kdp/launch-status.jsonl | tail -5
```

### Debug Individual Book

```bash
cat .runtime/kdp/The_Ultimate_Guide_*.json | jq '.uploads[] | {platform, success, error}'
```

## Compliance & Legal

### FTC Disclosure

If promoting affiliate products in your book:

```markdown
## Affiliate Disclosure

This book contains affiliate links. We may earn a commission if you purchase through these links, at no additional cost to you.
```

### Copyright Notice

Include in your book:

```markdown
© 2024 Already Here LLC. All rights reserved.

This book is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
```

### ISBNs

- **Free ISBNs:** Use Smashwords ISBN (free for Smashwords-published books)
- **Paid ISBNs:** Bowker.com ($125 single, $225 10-pack)
- **Platform-specific ISBNs:** Some platforms assign free ISBNs (KDP-assigned ISBNs don't work on other platforms)

## Next Steps

1. Set up environment variables
2. Create your first book file
3. Test cover generation
4. Publish to KDP
5. Wait 48 hours for indexing
6. Monitor sales on KDP dashboard
7. Publish to Draft2Digital & Smashwords
8. Track consolidated earnings across platforms
