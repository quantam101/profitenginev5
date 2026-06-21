# KDP Automation Guide

Complete eBook publishing automation for Amazon KDP, Draft2Digital, and Smashwords.

## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Validation & Risk Assessment](#validation--risk-assessment)
- [Integration with Master Orchestrator](#integration-with-master-orchestrator)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Features

### Core Publishing
- **Multi-Platform Publishing**: Publish to KDP, Draft2Digital, Smashwords simultaneously
- **Metadata Parsing**: Extract book metadata from markdown frontmatter
- **Cover Generation**: Auto-generate covers via Unsplash, Pexels, DALL-E, or Replicate
- **Content Formatting**: Platform-specific formatting for KDP (EPUB/PDF), D2D, and Smashwords
- **Batch Publishing**: Publish multiple books with quality validation
- **Royalty Tracking**: Monitor earnings by ASIN/ISBN

### Quality Assurance
- **Metadata Validation**: Comprehensive checks for title, author, description, keywords, price
- **Risk Assessment**: Multi-factor risk scoring (low/medium/high) with actionable warnings
- **Platform Recommendations**: Intelligent platform selection based on book characteristics
- **Error Recovery**: Batch-level error handling with detailed reporting

### Integration
- **REST API**: `/api/automation/kdp` with multiple operations
- **Master Orchestrator**: Task-based execution with dependency management
- **Dashboard Card**: Real-time publication stats and book status
- **Background Execution**: Non-blocking async publishing with progress tracking

## Quick Start

### 1. Set Environment Variables

```bash
# Required for any platform
KDP_ACCESS_TOKEN=your_amazon_kdp_api_token
DRAFT2DIGITAL_API_KEY=your_d2d_api_key
SMASHWORDS_API_KEY=your_smashwords_api_key

# Image generation (choose one)
IMAGE_GENERATION_API=unsplash  # or: pexels, dalle, replicate
UNSPLASH_API_KEY=your_key
PEXELS_API_KEY=your_key
OPENAI_API_KEY=your_key
REPLICATE_API_TOKEN=your_token

# Optional
AUTOMATION_API_TOKEN=your_automation_token
KDP_MAX_PUBLISH_BATCH_SIZE=10
KDP_ENABLE_QUALITY_CHECKS=true
```

### 2. Create Book Markdown Files

```markdown
---
title: "The Complete Guide to eBook Publishing"
subtitle: "Master Amazon KDP, Draft2Digital, and More"
author: "Jane Doe"
description: "Learn professional eBook publishing strategies."
category: "Business"
keywords: ["ebook", "publishing", "amazon-kdp", "self-publishing"]
price: 14.99
currency: "USD"
language: "en"
isbn: "978-1-234567-89-0"
publisher: "Self Published"
cover_image_prompt: "Modern professional book cover design"
---

# Chapter 1: Introduction

Your book content here...
```

Save as `KDP_BOOK_[title].md`

### 3. Use the API

```bash
# Publish books
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "batch-publish",
    "bookFiles": ["KDP_BOOK_guide.md", "KDP_BOOK_course.md"],
    "platforms": ["kdp", "draft2digital"]
  }'

# Validate before publishing
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "validate",
    "bookFiles": ["KDP_BOOK_guide.md"]
  }'

# Track royalties
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "track-royalties",
    "asin": "B0A1B2C3D4E5F6G7"
  }'
```

### 4. Dashboard Integration

Add to your Next.js page:

```typescript
import KdpAutomationCard from '@/app/components/KdpAutomationCard';

export default function DashboardPage() {
  return (
    <div>
      <KdpAutomationCard refreshInterval={300000} />
    </div>
  );
}
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KDP_ACCESS_TOKEN` | Yes | — | Amazon KDP API token |
| `DRAFT2DIGITAL_API_KEY` | No | — | Draft2Digital API key |
| `SMASHWORDS_API_KEY` | No | — | Smashwords API key |
| `IMAGE_GENERATION_API` | No | `unsplash` | Cover generation provider |
| `UNSPLASH_API_KEY` | Conditional | — | For Unsplash image search |
| `PEXELS_API_KEY` | Conditional | — | For Pexels image search |
| `OPENAI_API_KEY` | Conditional | — | For DALL-E image generation |
| `REPLICATE_API_TOKEN` | Conditional | — | For Stable Diffusion/FLUX |
| `AUTOMATION_API_TOKEN` | No | — | API authentication token |
| `KDP_MAX_PUBLISH_BATCH_SIZE` | No | `10` | Max books per batch |
| `KDP_ENABLE_QUALITY_CHECKS` | No | `true` | Validate before publishing |

### Book Metadata Fields

Required:
- `title` (3-100 characters)
- `author`
- `description` (20+ characters)
- `category`
- `keywords` (1+ items)
- `price` (0-99.99 USD)

Optional:
- `subtitle`
- `language` (default: en)
- `isbn`
- `publisher`
- `copyright_year`
- `series` (name, number)
- `cover_image_prompt`
- `publication_countries` (default: [US])

## API Endpoints

### POST /api/automation/kdp

#### publish | batch-publish
Publish one or more books to configured platforms.

**Request:**
```json
{
  "operation": "publish",
  "bookFiles": ["KDP_BOOK_guide.md"],
  "platforms": ["kdp", "draft2digital"],
  "validateOnly": false
}
```

**Response:**
```json
{
  "success": true,
  "runId": "kdp-publication-1718894823456",
  "operation": "publish",
  "booksProcessed": 1,
  "platformsPerBook": 2,
  "estimatedDuration": "100s",
  "status": "initiated",
  "timestamp": "2024-06-20T12:00:00Z",
  "duration": 45
}
```

#### validate
Validate book metadata without publishing.

**Request:**
```json
{
  "operation": "validate",
  "bookFiles": ["KDP_BOOK_guide.md"]
}
```

**Response:**
```json
{
  "success": true,
  "operation": "validate",
  "validationResults": {
    "total": 1,
    "successful": 1,
    "failed": 0,
    "validated": 1,
    "validationErrors": []
  },
  "timestamp": "2024-06-20T12:00:00Z",
  "duration": 12
}
```

#### track-royalties
Fetch royalty earnings for a published book.

**Request:**
```json
{
  "operation": "track-royalties",
  "asin": "B0A1B2C3D4E5F6G7"
}
```

**Response:**
```json
{
  "success": true,
  "operation": "track-royalties",
  "asin": "B0A1B2C3D4E5F6G7",
  "earnings": [
    {
      "period": "2024-06",
      "units": 15,
      "revenue": 150.00,
      "royaltyEarnings": 52.50,
      "currency": "USD"
    }
  ],
  "timestamp": "2024-06-20T12:00:00Z",
  "duration": 234
}
```

### GET /api/automation/kdp

Get KDP automation status.

**Query Parameters:**
- `asin` (optional): Get royalties for specific ASIN

**Response:**
```json
{
  "success": true,
  "status": "ready",
  "operations": ["publish", "track-royalties", "validate", "batch-publish"],
  "platforms": ["kdp", "draft2digital", "smashwords"],
  "configured": {
    "kdp": true,
    "draft2digital": false,
    "smashwords": false
  },
  "timestamp": "2024-06-20T12:00:00Z"
}
```

## Validation & Risk Assessment

### Metadata Validation Rules

| Field | Rule | Examples |
|-------|------|----------|
| Title | 3-100 characters | ✓ "Complete Guide" ✗ "AB" |
| Author | Required, non-empty | ✓ "Jane Doe" ✗ "" |
| Description | 20+ characters | ✓ "Learn..." ✗ "A book" |
| Category | Required | ✓ "Business" ✗ "" |
| Keywords | 1+ required | ✓ ["ebook"] ✗ [] |
| Price | 0.01-99.99 USD | ✓ 14.99 ✗ 0 or 150 |
| Language | Supported ISO codes | ✓ "en" ✗ "xx" |

### Risk Scoring (0-100)

Low Risk (0-19):
- Complete metadata with all recommended fields
- Appropriate price point ($9.99+)
- Common category
- 3+ keywords
- 50+ character description

Medium Risk (20-39):
- Some optional fields missing
- Non-standard category
- Low price ($2.99-4.99)
- 2 keywords only
- Borderline description length

High Risk (40+):
- Missing critical fields
- Very short title (<5 chars)
- Very short description (<50 chars)
- No keywords
- Very low price (<$2.99)
- ISBN not provided

### Risk Example

```typescript
import { assessPublicationRisk } from '@/app/lib/automation/kdp';

const result = assessPublicationRisk(metadata);
// {
//   riskLevel: 'medium',
//   score: 25,
//   warnings: [
//     'Description may be too brief for optimal discoverability',
//     'Fewer than 3 keywords provided',
//     'ISBN not provided (optional but recommended)'
//   ]
// }
```

## Integration with Master Orchestrator

### Task-Based Publishing

```typescript
import { MasterOrchestrator } from '@/app/lib/automation/master-orchestrator';
import {
  createKdpPublishTask,
  createKdpValidationTask,
  createKdpRoyaltyTask,
  routeKdpTask,
} from '@/app/lib/automation/kdp-orchestrator-integration';

// Create orchestrator
const orchestrator = new MasterOrchestrator({
  mode: 'smart',
  tasks: [
    createKdpValidationTask({
      bookFiles: ['KDP_BOOK_guide.md'],
      priority: 'high',
    }),
    createKdpPublishTask({
      bookFiles: ['KDP_BOOK_guide.md'],
      platforms: ['kdp', 'draft2digital'],
      priority: 'high',
      dependencies: [
        { taskId: 'kdp-validate-...', required: true }
      ],
    }),
  ],
});

// Register KDP task executor
orchestrator.registerTaskExecutor('kdp-publish', routeKdpTask);
orchestrator.registerTaskExecutor('kdp-validate', routeKdpTask);
orchestrator.registerTaskExecutor('kdp-royalties', routeKdpTask);

// Execute
const results = await orchestrator.execute();
```

## Examples

### Example 1: Simple Single Book Publishing

```typescript
import { orchestrateKdpPublication } from '@/app/lib/automation/kdp';

const result = await orchestrateKdpPublication();
// Publishes all KDP_BOOK_*.md files found in current directory
```

### Example 2: Validate with Risk Assessment

```typescript
import {
  validateBookMetadata,
  assessPublicationRisk,
  parseBookMetadata,
} from '@/app/lib/automation/kdp';

const metadata = await parseBookMetadata('KDP_BOOK_guide.md');

// Validate
const validation = validateBookMetadata(metadata);
if (!validation.valid) {
  console.error('Validation errors:', validation.errors);
  return;
}

// Assess risk
const risk = assessPublicationRisk(metadata);
if (risk.riskLevel === 'high') {
  console.warn('High-risk publication:', risk.warnings);
}

// Proceed with publication...
```

### Example 3: Batch Publishing with Platform Selection

```typescript
import { batchPublishBooks } from '@/app/lib/automation/kdp';

const result = await batchPublishBooks(
  ['KDP_BOOK_1.md', 'KDP_BOOK_2.md', 'KDP_BOOK_3.md'],
  {
    validateOnly: false,
    platforms: ['kdp', 'draft2digital'],
    maxBatchSize: 5,
  }
);

console.log(`Published: ${result.successful}/${result.total}`);
if (result.validationErrors.length > 0) {
  console.error('Validation errors:', result.validationErrors);
}
```

### Example 4: Royalty Tracking Automation

```typescript
import { trackKdpRoyalties } from '@/app/lib/automation/kdp';

const asins = ['B0A1B2C3D4E5F6G7', 'B0B2C3D4E5F6G7H8'];
const allEarnings = [];

for (const asin of asins) {
  const earnings = await trackKdpRoyalties(asin);
  allEarnings.push({ asin, earnings });
}

const totalRevenue = allEarnings.reduce((sum, item) => {
  const itemTotal = item.earnings.reduce((s, e) => s + (e.royaltyEarnings || 0), 0);
  return sum + itemTotal;
}, 0);

console.log(`Total royalties: $${totalRevenue.toFixed(2)}`);
```

## Troubleshooting

### API Authentication Failed

**Error**: `Unauthorized`

**Solution**:
```bash
# Verify token is set correctly
echo $AUTOMATION_API_TOKEN

# Use Bearer scheme
Authorization: Bearer your_token_here

# Not: Authorization: your_token_here
```

### Cover Generation Failed

**Error**: `Cover generation failed`

**Solutions**:
- Check image provider API key is set
- Verify UNSPLASH_API_KEY, OPENAI_API_KEY, etc.
- Fallback: Provide `coverImageUrl` in metadata
- Use simpler `cover_image_prompt` if DALL-E fails

### Metadata Validation Errors

**Error**: `Description should be at least 20 characters`

**Solution**: Expand book description in markdown frontmatter:
```markdown
---
description: "Comprehensive guide covering all aspects of..."
---
```

### Draft2Digital Upload Failed

**Error**: `Draft2Digital API error: [400]`

**Solutions**:
- Verify DRAFT2DIGITAL_API_KEY is correct
- Check description is valid HTML (formatted by system)
- Ensure ISBN format is correct (if provided)

### Batch Publishing Timeout

**Error**: `Task timeout: 600000ms`

**Solution**: Increase timeout or reduce batch size:
```bash
# Increase global timeout
AUTOMATION_CIRCUIT_BREAKER_RESET_MS=900000

# Or reduce batch
KDP_MAX_PUBLISH_BATCH_SIZE=5
```

### Memory Issues with Large Batches

**Error**: Memory usage spike during batch publishing

**Solutions**:
- Reduce batch size: `KDP_MAX_PUBLISH_BATCH_SIZE=3`
- Process books sequentially instead of parallel
- Increase Node.js memory: `NODE_OPTIONS=--max_old_space_size=4096`

## Performance Metrics

Typical performance on standard hardware:

| Operation | Time | Notes |
|-----------|------|-------|
| Metadata Validation | 10-20ms | Per book |
| Risk Assessment | 5-10ms | Per book |
| Cover Generation | 500-5000ms | Depends on provider |
| KDP Upload | 1000-3000ms | Per book |
| Draft2Digital Upload | 800-2000ms | Per book |
| Smashwords Upload | 1000-3000ms | Per book |
| Batch Publishing (3 books) | 15-30 seconds | All 3 platforms |

## Support

For issues or feature requests, create a GitHub issue with:
- Error message and stack trace
- Environment configuration (sanitized)
- Steps to reproduce
- Expected vs actual behavior
