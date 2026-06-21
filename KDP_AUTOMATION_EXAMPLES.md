# KDP Automation — Examples & Test Cases

## Quick Examples

### Example 1: Publish a Single Book via API

```bash
# Set up environment
export OPENAI_API_KEY="sk-..."
export KDP_ACCESS_TOKEN="your-token"
export DRAFT2DIGITAL_API_KEY="your-key"
export SMASHWORDS_API_KEY="your-key"

# Create a book file
cat > KDP_BOOK_myguide.md << 'EOF'
---
title: My First Guide
author: Jane Doe
description: A practical guide
category: Business
price: 9.99
keywords: [guide, business, marketing]
cover_image_prompt: Professional business book cover with modern design
---

# Chapter 1

Your content here.
EOF

# Publish via API
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
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
  "booksProcessed": 1,
  "platformsPerBook": 3,
  "estimatedDuration": "100s",
  "status": "initiated"
}
```

### Example 2: Track Royalties for a Published Book

```bash
# Get earnings for an ASIN
curl "http://localhost:3000/api/automation/kdp?asin=B0A1B2C3D4E5F6G7" \
  -H "Authorization: Bearer your-token"
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
      "units": 45,
      "revenue": 449.55,
      "royaltyRate": 0.35,
      "royaltyEarnings": 157.34,
      "currency": "USD"
    },
    {
      "asin": "B0A1B2C3D4E5F6G7",
      "platform": "kdp",
      "period": "2024-07",
      "units": 72,
      "revenue": 719.28,
      "royaltyRate": 0.35,
      "royaltyEarnings": 251.75,
      "currency": "USD"
    }
  ]
}
```

### Example 3: Batch Publish Multiple Books

```bash
# Create multiple book files
cat > KDP_BOOK_course1.md << 'EOF'
---
title: Course Complete System
author: Jane Doe
description: Full system for online courses
category: Education
price: 19.99
---
# Content...
EOF

cat > KDP_BOOK_course2.md << 'EOF'
---
title: Advanced Strategies
author: Jane Doe
description: Deep dive into advanced methods
category: Business
price: 24.99
---
# Content...
EOF

# Publish all at once
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "publish",
    "bookFiles": ["KDP_BOOK_course1.md", "KDP_BOOK_course2.md"],
    "platforms": ["kdp", "draft2digital"]
  }'
```

---

## TypeScript Usage Examples

### Example 4: Programmatic Publishing in Next.js

```typescript
// pages/api/publish-book.ts
import { orchestrateKdpPublication } from '@/app/lib/automation/kdp';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const results = await orchestrateKdpPublication();
    
    return res.status(200).json({
      success: true,
      booksPublished: results.length,
      successfulPublications: results.filter(r => r.overallSuccess).length,
      results,
    });
  } catch (error) {
    return res.status(500).json({
      error: error instanceof Error ? error.message : 'Publication failed',
    });
  }
}
```

### Example 5: Publish Single Book with Custom Settings

```typescript
import {
  parseBookMetadata,
  generateBookCover,
  uploadToKdp,
  uploadToDraft2Digital,
  uploadToSmashwords,
} from '@/app/lib/automation/kdp';

async function publishMyBook() {
  // Parse metadata
  const metadata = await parseBookMetadata('KDP_BOOK_myguide.md');
  
  console.log(`Publishing: ${metadata.title}`);
  console.log(`Author: ${metadata.author}`);
  console.log(`Price: $${metadata.price}`);
  
  // Generate cover
  console.log('Generating cover image...');
  const coverUrl = await generateBookCover(metadata);
  console.log(`✓ Cover generated: ${coverUrl}`);
  
  // Upload to KDP
  console.log('Uploading to Amazon KDP...');
  const kdpResult = await uploadToKdp(metadata, coverUrl);
  if (kdpResult.success) {
    console.log(`✓ Published on KDP: ${kdpResult.asin}`);
  }
  
  // Upload to Draft2Digital
  console.log('Uploading to Draft2Digital...');
  const d2dResult = await uploadToDraft2Digital(metadata, coverUrl);
  if (d2dResult.success) {
    console.log(`✓ Published on Draft2Digital: ${d2dResult.bookId}`);
  }
  
  // Upload to Smashwords
  console.log('Uploading to Smashwords...');
  const swResult = await uploadToSmashwords(metadata, coverUrl);
  if (swResult.success) {
    console.log(`✓ Published on Smashwords: ${swResult.bookId}`);
  }
  
  return {
    metadata,
    coverUrl,
    uploads: [kdpResult, d2dResult, swResult],
  };
}

// Run it
publishMyBook().catch(console.error);
```

### Example 6: Custom Cover Generation

```typescript
import { generateBookCover } from '@/app/lib/automation/kdp';

async function generateCoversForAllBooks() {
  const books = [
    {
      title: 'Financial Freedom Guide',
      author: 'Jane Doe',
      category: 'Finance',
      coverImagePrompt: 'Professional finance book cover with money and charts, gold and blue colors, luxury design'
    },
    {
      title: 'Marketing Mastery',
      author: 'Jane Doe',
      category: 'Marketing',
      coverImagePrompt: 'Modern marketing book cover with digital elements, bright colors, contemporary style'
    },
  ];
  
  for (const book of books) {
    console.log(`Generating cover for: ${book.title}`);
    const coverUrl = await generateBookCover(book as any);
    console.log(`✓ ${book.title}: ${coverUrl}`);
    
    // Save URL for later use
    console.log(`Cover URL: ${coverUrl}`);
  }
}

generateCoversForAllBooks();
```

### Example 7: Track Earnings Dashboard

```typescript
import { trackKdpRoyalties } from '@/app/lib/automation/kdp';

async function buildRoyaltiesDashboard() {
  // Your published ASINs
  const asins = [
    'B0A1B2C3D4E5F6G7',
    'B0A1B2C3D4E5F6G8',
    'B0A1B2C3D4E5F6G9',
  ];
  
  let totalEarnings = 0;
  let totalUnits = 0;
  
  console.log('=== KDP ROYALTIES DASHBOARD ===\n');
  
  for (const asin of asins) {
    const earnings = await trackKdpRoyalties(asin);
    
    const totalByAsin = earnings.reduce((sum, e) => sum + e.royaltyEarnings, 0);
    const unitsByAsin = earnings.reduce((sum, e) => sum + e.units, 0);
    
    console.log(`ASIN: ${asin}`);
    console.log(`  Units: ${unitsByAsin}`);
    console.log(`  Earnings: $${totalByAsin.toFixed(2)}`);
    console.log();
    
    totalEarnings += totalByAsin;
    totalUnits += unitsByAsin;
  }
  
  console.log('=== TOTAL ===');
  console.log(`Units: ${totalUnits}`);
  console.log(`Total Earnings: $${totalEarnings.toFixed(2)}`);
  console.log(`Average per Unit: $${(totalEarnings / totalUnits).toFixed(2)}`);
}

buildRoyaltiesDashboard();
```

---

## Test Cases & Validation

### Test 1: Metadata Parsing

```typescript
import { parseBookMetadata } from '@/app/lib/automation/kdp';

async function testMetadataParsing() {
  try {
    const metadata = await parseBookMetadata('KDP_BOOK_affiliate_mastery.md');
    
    // Assertions
    console.assert(metadata.title === 'Affiliate Marketing Mastery');
    console.assert(metadata.author === 'Stephen Franklin');
    console.assert(metadata.price === 14.99);
    console.assert(metadata.keywords.length >= 5);
    console.assert(metadata.longDescription.length > 500);
    
    console.log('✓ Metadata parsing test passed');
    return true;
  } catch (error) {
    console.error('✗ Metadata parsing test failed:', error);
    return false;
  }
}

testMetadataParsing();
```

### Test 2: Content Formatting

```typescript
import {
  formatContentForKdp,
  formatContentForDraft2Digital,
  formatContentForSmashwords,
} from '@/app/lib/automation/kdp';

async function testContentFormatting() {
  const content = `
# Introduction

This is **bold** and *italic* text.

## Chapter 1

- List item 1
- List item 2

[Link](https://example.com)

\`\`\`javascript
const x = 1;
\`\`\`
`;

  // Test KDP formatting
  const kdpFormatted = formatContentForKdp(content);
  console.assert(!kdpFormatted.includes('<script>'));
  console.assert(!kdpFormatted.includes('<iframe>'));
  console.log('✓ KDP formatting passed');

  // Test Draft2Digital formatting
  const d2dFormatted = formatContentForDraft2Digital(content);
  console.assert(d2dFormatted.includes('<strong>'));
  console.assert(d2dFormatted.includes('<em>'));
  console.log('✓ Draft2Digital formatting passed');

  // Test Smashwords formatting
  const swFormatted = formatContentForSmashwords(content);
  console.assert(swFormatted.length > 0);
  console.log('✓ Smashwords formatting passed');
}

testContentFormatting();
```

### Test 3: Cover Generation (Dry Run)

```typescript
// Before running this test, ensure environment variables are set
import { generateBookCover } from '@/app/lib/automation/kdp';

async function testCoverGeneration() {
  const testBook = {
    title: 'Test Book',
    author: 'Test Author',
    description: 'A test book',
    category: 'Business',
    keywords: [],
    price: 9.99,
    coverImagePrompt: 'Professional book cover with test design'
  };

  try {
    console.log('Generating test cover...');
    const coverUrl = await generateBookCover(testBook as any);
    
    console.assert(coverUrl.startsWith('http'));
    console.assert(coverUrl.length > 20);
    
    console.log('✓ Cover generation test passed');
    console.log(`Generated URL: ${coverUrl}`);
    return true;
  } catch (error) {
    console.warn('⚠ Cover generation test failed (API may not be configured):', error);
    return false;
  }
}

testCoverGeneration();
```

### Test 4: API Endpoint

```bash
# Test publication endpoint
curl -X POST http://localhost:3000/api/automation/kdp \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "publish"
  }' | jq '.success'

# Expected response: true

# Test status endpoint
curl http://localhost:3000/api/automation/kdp | jq '.status'

# Expected response: "ready"

# Test royalty tracking endpoint
curl "http://localhost:3000/api/automation/kdp?asin=INVALID" | jq '.success'

# Expected response: false (invalid ASIN)
```

---

## Debugging Examples

### Debug 1: Check Environment Variables

```bash
# Verify all required environment variables are set
echo "IMAGE_GENERATION_API: $IMAGE_GENERATION_API"
echo "KDP_ACCESS_TOKEN: ${KDP_ACCESS_TOKEN:0:20}..."
echo "DRAFT2DIGITAL_API_KEY: ${DRAFT2DIGITAL_API_KEY:0:20}..."
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."

# All should print values (partially hidden for security)
```

### Debug 2: Inspect Book Metadata

```typescript
import { parseBookMetadata } from '@/app/lib/automation/kdp';

async function debugBookMetadata() {
  const metadata = await parseBookMetadata('KDP_BOOK_affiliate_mastery.md');
  
  console.log('=== BOOK METADATA DEBUG ===');
  console.log(JSON.stringify(metadata, null, 2));
  
  // Check for issues
  if (!metadata.title) console.error('✗ Missing title');
  if (!metadata.author) console.error('✗ Missing author');
  if (metadata.price < 2.99) console.error('✗ Price too low for KDP');
  if (metadata.price > 999.99) console.error('✗ Price too high for KDP');
  if (metadata.keywords.length > 7) console.error('✗ Too many keywords for KDP (max 7)');
  if (!metadata.longDescription) console.warn('⚠ Missing content body');
}

debugBookMetadata();
```

### Debug 3: Validate API Response

```typescript
async function debugApiResponse() {
  const response = await fetch('http://localhost:3000/api/automation/kdp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer your-token'
    },
    body: JSON.stringify({
      operation: 'publish'
    })
  });

  const data = await response.json();
  
  console.log('Status:', response.status);
  console.log('Response:', JSON.stringify(data, null, 2));
  
  // Validate response structure
  if (!data.success) {
    console.error('✗ Publication failed:', data.error);
  } else {
    console.log('✓ Publication initiated');
    console.log(`  Run ID: ${data.runId}`);
    console.log(`  Estimated duration: ${data.estimatedDuration}`);
  }
}

debugApiResponse();
```

### Debug 4: Check Publication Results

```bash
# View latest publication result
cat .runtime/kdp/publication-summary_*.json | tail -1 | jq '.'

# View all successful publications
cat .runtime/kdp/*.json | jq 'select(.overallSuccess == true) | {title: .metadata.title, platforms: [.uploads[].platform]}'

# Count total uploads
cat .runtime/kdp/*.json | jq '[.uploads[] | select(.success == true)] | length'

# View failures
cat .runtime/kdp/*.json | jq '.uploads[] | select(.success == false)'
```

---

## Performance Optimization

### Example: Batch Processing with Limits

```typescript
async function publishBooksWithRateLimit(fileNames: string[], maxConcurrent = 2) {
  console.log(`Publishing ${fileNames.length} books, max ${maxConcurrent} concurrent...`);
  
  for (let i = 0; i < fileNames.length; i += maxConcurrent) {
    const batch = fileNames.slice(i, i + maxConcurrent);
    
    console.log(`\nBatch ${Math.floor(i / maxConcurrent) + 1}:`);
    
    const results = await Promise.all(
      batch.map(async (fileName) => {
        try {
          const metadata = await parseBookMetadata(fileName);
          const cover = await generateBookCover(metadata);
          const kdpResult = await uploadToKdp(metadata, cover);
          return { fileName, success: kdpResult.success };
        } catch (error) {
          return { fileName, success: false, error };
        }
      })
    );
    
    results.forEach(r => {
      console.log(`  ${r.fileName}: ${r.success ? '✓' : '✗'}`);
    });
    
    // Wait before next batch
    if (i + maxConcurrent < fileNames.length) {
      console.log('Waiting 30s before next batch...');
      await new Promise(resolve => setTimeout(resolve, 30000));
    }
  }
}

// Usage
publishBooksWithRateLimit(['KDP_BOOK_1.md', 'KDP_BOOK_2.md', 'KDP_BOOK_3.md'], 2);
```

---

## Integration with Orchestration

### Example: Integrate KDP into Full Automation

```typescript
// app/lib/automation/orchestrate.ts
import { orchestrateKdpPublication } from './kdp';

// Add to task list
const kdpTask: AutomationTask = {
  name: 'KDP Publication',
  type: 'kdp' as any,
  enabled: process.env.KDP_ACCESS_TOKEN ? true : false,
  retryMaxAttempts: 3,
};

// Add to executeTask function
if (task.type === 'kdp') {
  result = await orchestrateKdpPublication();
}
```

This integrates KDP publishing into the main automation orchestration, alongside Gumroad, Instagram, and email.

---

## Production Checklist

Before publishing books in production:

- [ ] All environment variables configured
- [ ] Test book file created and validated
- [ ] Cover image generation tested
- [ ] API endpoints responding correctly
- [ ] Metadata parsing working for sample file
- [ ] KDP/D2D/Smashwords API tokens verified
- [ ] Content formatting tested for each platform
- [ ] Results storage directory exists (.runtime/kdp/)
- [ ] Logging configured and verified
- [ ] Error handling tested with invalid inputs
- [ ] Rate limiting verified if publishing multiple books
- [ ] Royalty tracking tested with valid ASIN

Once all checks pass, you're ready to publish books to production!
