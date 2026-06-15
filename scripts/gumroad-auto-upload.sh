#!/bin/bash

# GUMROAD AUTOMATIC PRODUCT UPLOAD
# Creates 4 products with PDFs on Gumroad
# Usage: bash gumroad-auto-upload.sh

set -e

# Configuration
GUMROAD_TOKEN="alynEcVBjH8tPrFgxbwLLxP2hpKlSlqqaVOTcvoPSYk"
GUMROAD_USERNAME="alreadyhere"
API_URL="https://api.gumroad.com/v2"

echo "🚀 Starting Gumroad Product Upload..."
echo "Username: $GUMROAD_USERNAME"
echo ""

# Product 1: Master Blueprint
echo "📦 Creating Product 1: Master Blueprint..."
curl -X POST "$API_URL/products" \
  -H "Authorization: Bearer $GUMROAD_TOKEN" \
  -d "name=Master Blueprint: Build a \$600K Business in 90 Days" \
  -d "description=The complete 4-stream business system with everything you need. 7 chapters covering all revenue streams, real numbers from Month 1, institutional partnership scripts, vehicle recovery sourcing & flipping guide, gig work contractor model, content monetization strategy, 90-day action plan." \
  -d "price=12700" \
  -d "currency=usd" \
  -d "summary=Complete 4-stream business system with proven playbooks and real numbers"

echo "✅ Product 1 created"
echo ""

# Product 2: Institutional Playbook
echo "📦 Creating Product 2: Institutional Partnerships Playbook..."
curl -X POST "$API_URL/products" \
  -H "Authorization: Bearer $GUMROAD_TOKEN" \
  -d "name=Institutional Partnerships Playbook" \
  -d "description=Complete system for landing nonprofit/government fleet contracts. 26 Phoenix organizations, email scripts that get responses, phone call framework, proposal templates, objection handling, deal evaluation checklist, first 30 days onboarding plan, real contract examples." \
  -d "price=7200" \
  -d "currency=usd" \
  -d "summary=26 prospects + sales scripts to land your first \$25K contract"

echo "✅ Product 2 created"
echo ""

# Product 3: Vehicle Recovery
echo "📦 Creating Product 3: Vehicle Recovery & Fix-and-Flip Guide..."
curl -X POST "$API_URL/products" \
  -H "Authorization: Bearer $GUMROAD_TOKEN" \
  -d "name=Vehicle Recovery & Fix-and-Flip: The Complete Guide" \
  -d "description=How to find cheap cars, repair them for \$1,500, and flip for \$3,500-\$6,000. 5 ways to source cars, deal evaluation scorecard, repair budget breakdown, where to find parts cheap, sales strategies, real examples with actual numbers, scaling to 8-12 cars/month, profit calculator." \
  -d "price=5700" \
  -d "currency=usd" \
  -d "summary=Find cars for \$500, flip for \$5,000+. Complete sourcing + flipping guide."

echo "✅ Product 3 created"
echo ""

# Product 4: Gig Work System
echo "📦 Creating Product 4: Gig Work System & Scaling to 50/Month..."
curl -X POST "$API_URL/products" \
  -H "Authorization: Bearer $GUMROAD_TOKEN" \
  -d "name=Gig Work System: High-Margin Jobs + Scaling to 50/Month" \
  -d "description=The complete system for 75%+ margin gig work. 5 high-margin job types, pricing strategy for \$800-\$1,500 jobs, contractor recruitment & vetting, two-tier contractor model, demand generation across 5 channels, fleet economics, operations checklist, scaling to 30-50 jobs/month." \
  -d "price=5700" \
  -d "currency=usd" \
  -d "summary=High-margin jobs with contractors. Scale from 0 to 50 jobs/month."

echo "✅ Product 4 created"
echo ""

echo "🎉 All products created!"
echo ""
echo "📍 View your products at: https://alreadyhere.gumroad.com"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Go to alreadyhere.gumroad.com"
echo "2. For each product, upload the PDF file"
echo "3. Set to 'Deliver automatically'"
echo "4. Products will be live immediately"
echo ""
echo "🔒 SECURITY: Rotate your API token after upload:"
echo "   Gumroad → Settings → API → Regenerate Token"
