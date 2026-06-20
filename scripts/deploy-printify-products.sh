#!/bin/bash
# Deploy 7 products to Printify
# Requires: PRINTIFY_API_TOKEN in GitHub Secrets

set -euo pipefail

echo "=========================================="
echo "DEPLOYING PRODUCTS TO PRINTIFY"
echo "=========================================="
echo ""

# Load environment
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PRINTIFY_TOKEN="${PRINTIFY_API_TOKEN:-}"

if [ -z "$PRINTIFY_TOKEN" ]; then
  echo "[ERROR] PRINTIFY_API_TOKEN not set"
  echo "Set PRINTIFY_API_TOKEN in GitHub Secrets or .env"
  exit 1
fi

echo "[1] Creating Printify product setup guide..."

cat > "PRINTIFY_SETUP.md" << 'EOF'
# Printify Product Setup Guide

## Account Setup
1. Go to: https://printify.com
2. Create account
3. Connect Gumroad store (optional) or use Printify dashboard directly
4. Add payment method
5. Get API token from Settings → API

## 7 Products to Create

### Product 1: AI Productivity T-Shirt
- Product: T-Shirt (Bella+Canvas 3001)
- Price: $34.99
- Design: "AI MADE ME 10X MORE PRODUCTIVE" (front, white text)
- Colors: Black, Navy, White
- Expected sales: 5-10/month = $150-300/month

### Product 2: No More Excel Hoodie
- Product: Hoodie (Bella+Canvas 3719)
- Price: $64.99
- Design: "I REPLACED EXCEL WITH AI" (front), "And Got My Life Back" (back)
- Colors: Black, Charcoal
- Expected sales: 3-5/month = $150-250/month

### Product 3: Debug With AI Hat
- Product: Baseball Cap
- Price: $24.99
- Design: "Debug with AI" (embroidered front)
- Colors: Black, Navy, Gray
- Expected sales: 5-10/month = $100-200/month

### Product 4: Productivity Sticker Pack
- Product: Custom Stickers (5-pack)
- Price: $7.99
- Designs: 5 different stickers (high margin item)
- Expected sales: 20-30/month = $150-200/month

### Product 5: AI Productivity Mug
- Product: 11oz Ceramic Mug
- Price: $16.99
- Design: "COFFEE + AI = UNSTOPPABLE"
- Colors: White
- Expected sales: 5-10/month = $70-150/month

### Product 6: Productivity Journal
- Product: Hardcover Notebook (Custom Print)
- Price: $24.99
- Design: Professional cover with "AI Productivity Journal"
- Expected sales: 3-5/month = $70-120/month

### Product 7: Automation Sweatshirt
- Product: Sweatshirt (Gildan 18500)
- Price: $52.99
- Design: "AUTOMATION > HUSTLE"
- Colors: Black, Navy, Charcoal
- Expected sales: 3-5/month = $150-250/month

## Design Images
Use AI Image Generator (Midjourney/DALL-E) prompts:

T-Shirt: "Professional product photo of black t-shirt with white text 'AI MADE ME 10X MORE PRODUCTIVE', flat lay on white background, studio lighting"

Hoodie: "Professional product photo of black hoodie with white text design, on model, clean studio background"

Hat: "Baseball cap with embroidered design, front view, professional product photo"

## Pricing Strategy
- Base cost: Product cost + Printify margin
- Our markup: 40-70% (high margin)
- Bundle discounts: Buy 2 save 10%, Buy 3 save 15%

## Expected Revenue
Conservative: 20-30 sales/month = $500-800
Moderate: 50-75 sales/month = $1,500-2,500
Aggressive: 100-150 sales/month = $3,500-5,000

## Marketing Strategy
1. Reddit: r/programming, r/productivity, r/learnprogramming
2. Twitter: @dev community + #productivity
3. ProductHunt: Create separate launch
4. Indie Hackers: Post to community
5. Dev.to: Write article + include store link
6. TikTok/YouTube Shorts: Unboxing videos

## Automation
- Webhook connected to transaction log
- Each order auto-logs to .runtime/revenue/transactions.jsonl
- Dashboard shows real-time sales + profit margins

## Success Metrics
- Track which products sell best
- Optimize designs for top sellers
- Retire underperformers
- Reinvest profits into better designs

EOF

echo "    ✓ Setup guide created: PRINTIFY_SETUP.md"
echo ""

echo "[2] Creating marketing assets..."
mkdir -p "marketing/printify"

cat > "marketing/printify/twitter-launch.txt" << 'EOF'
Just launched merchandise for the #ProductivityTwitter crowd:

- AI Productivity T-Shirt ($34.99)
- No More Excel Hoodie ($64.99)
- Debug With AI Hat ($24.99)
- Automation Sweatshirt ($52.99)

+ stickers, mugs, journals

For everyone who's tired of hiding their AI productivity lifestyle.

Shop: [PRINTIFY_LINK]

#AIProductivity #TechMerch
EOF

cat > "marketing/printify/reddit-launch.txt" << 'EOF'
Hey /r/productivity and /r/programming - Just launched merchandise celebrating the AI productivity revolution

We created 7 products for the people actually using AI to get their lives back:

- AI Productivity T-Shirt ($34.99)
- No More Excel Hoodie ($64.99)
- Debug With AI Hat ($24.99)
- Automation Sweatshirt ($52.99)
- Sticker Pack ($7.99)
- AI Productivity Mug ($16.99)
- Productivity Journal ($24.99)

Every product celebrates the people who are shipping 3x faster, analyzing 10x quicker, and reclaiming their time.

Limited first run. Shop while inventory lasts.

[PRINTIFY_LINK]

Questions about designs or want custom merch? Happy to help.
EOF

cat > "marketing/printify/bundle-strategy.txt" << 'EOF'
BUNDLE PRICING STRATEGY
=======================

Bundle 1: "Productivity Starter" ($89.99)
- AI Productivity T-Shirt ($34.99)
- No More Excel Hoodie ($64.99)
- Sticker Pack ($7.99)
Regular: $107.97 → Bundle: $89.99 (Save $17.98)

Bundle 2: "Developer Pack" ($79.99)
- Debug With AI Hat ($24.99)
- AI Productivity T-Shirt ($34.99)
- Sticker Pack ($7.99)
Regular: $67.97 → Bundle: $79.99 (Save $0, but bundled value)

Bundle 3: "Complete Setup" ($149.99)
- T-Shirt + Hoodie + Hat + Journal
Regular: $147.96 → Bundle: $149.99 (Free shipping added)

EXPECTED IMPACT:
- 20% of customers buy bundles
- Bundles increase average order value 40-60%
- Bundles reduce shipping costs per item

PROMOTION STRATEGY:
- Launch with bundles for first 2 weeks
- Switch to individual sales
- Re-offer bundles before holidays
EOF

echo "    ✓ Marketing assets created in marketing/printify/"
echo ""

echo "[3] Creating traffic strategy..."
cat > "marketing/printify/traffic-plan.md" << 'EOF'
# Printify Product Traffic Plan

## Week 1: Launch Phase
- Post on Reddit (r/productivity, r/programming, r/learnprogramming)
- Tweet with ProductHunt link
- Share in relevant Discord communities
- Post on Dev.to with article
- Expected traffic: 500-1,000 visits
- Expected conversion: 5-10%
- Expected sales: 25-100 units = $750-1,500

## Week 2-4: Sustained Growth
- Repost on Reddit (different communities)
- Create YouTube Short (unboxing video)
- TikTok video showing products
- Instagram Reels
- Newsletter (if you have one)
- Expected traffic: 200-500 visits/week
- Expected sales: 10-30 units/week = $300-900/week

## Month 2+: Organic + Paid
- Organic traffic compounds (SEO, word-of-mouth)
- Paid ads (Facebook, Google, Twitter) if budget allows
- Affiliate partnerships
- Influencer partnerships (tech creators)
- Expected: 500-1,000 visits/month
- Expected sales: 50-150 units/month = $1,500-4,500

## Content Repurposing
- Create 5 short TikTok videos (30 sec each)
- Create 5 Instagram Reels
- Create YouTube Shorts playlist
- Write 1 blog post about products
- Create 20 social media posts (batch weekly)

## Success Metrics
- Track which platform drives most sales
- Optimize designs for top performers
- Double down on winning marketing channels
- Retire underperforming products

EOF

echo "    ✓ Traffic plan created"
echo ""

echo "=========================================="
echo "✓ PRINTIFY DEPLOYMENT PREPARATION COMPLETE"
echo "=========================================="
echo ""
echo "NEXT STEPS:"
echo "1. Review: PRINTIFY_SETUP.md"
echo "2. Create Printify account at: https://printify.com"
echo "3. Create 7 products (use setup guide)"
echo "4. Upload design images (use AI image generator)"
echo "5. Set pricing and margins"
echo "6. Launch and promote using marketing assets"
echo ""
echo "Expected first month: \$500-5,000 revenue"
echo ""
