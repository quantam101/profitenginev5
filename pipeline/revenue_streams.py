"""
Already Here LLC — Automated Revenue Streams
Stripe payment links, retainer packages, and lead platform config.
Run: python pipeline/revenue_streams.py to print all links and setup instructions.
"""

# ── Service menu with Stripe-ready pricing ────────────────────────────────────

SERVICES = {
    # One-time services
    "network_audit": {
        "name": "Network Infrastructure Audit",
        "price_usd": 350,
        "type": "one_time",
        "description": "On-site WiFi/network audit. Covers signal mapping, switch bottlenecks, failover gaps. Credit toward any remediation.",
        "delivery": "Same-day findings report",
        "stripe_product": "Already Here LLC — Network Audit ($350)",
    },
    "drone_standard": {
        "name": "Commercial Drone Survey — Standard",
        "price_usd": 750,
        "type": "one_time",
        "description": "Orthomosaic map, surface measurements, 4K stills. 48-hour delivery. Up to 1 acre.",
        "delivery": "48 hours after flight",
        "stripe_product": "Already Here LLC — Drone Survey Standard ($750)",
    },
    "drone_premium": {
        "name": "Commercial Drone Survey — Premium",
        "price_usd": 1200,
        "type": "one_time",
        "description": "Full orthomosaic, shade analysis, DEM, 4K video, stakeholder deck. Up to 5 acres.",
        "delivery": "48 hours after flight",
        "stripe_product": "Already Here LLC — Drone Survey Premium ($1,200)",
    },
    "cabling_quote": {
        "name": "Cabling Site Assessment + Fixed-Price Quote",
        "price_usd": 0,
        "type": "free",
        "description": "Free on-site assessment. Fixed-price Cat6/Cat7 cabling quote delivered within 24 hours.",
        "delivery": "24 hours",
        "stripe_product": None,
    },

    # Monthly recurring retainers — THE AUTO-INCOME ENGINE
    "retainer_bronze": {
        "name": "IT Support Retainer — Bronze",
        "price_usd": 199,
        "type": "monthly",
        "description": "2 hours remote support/month, priority email response, network health check quarterly.",
        "ideal_for": "Small offices 1-5 users",
        "stripe_product": "Already Here LLC — IT Retainer Bronze ($199/mo)",
    },
    "retainer_silver": {
        "name": "IT Support Retainer — Silver",
        "price_usd": 399,
        "type": "monthly",
        "description": "5 hours remote + onsite support/month, priority phone response, monthly network check, same-day dispatch for critical issues.",
        "ideal_for": "Mid offices 5-20 users",
        "stripe_product": "Already Here LLC — IT Retainer Silver ($399/mo)",
    },
    "retainer_gold": {
        "name": "IT Support Retainer — Gold",
        "price_usd": 699,
        "type": "monthly",
        "description": "Unlimited remote support, 8 hours onsite/month, quarterly infrastructure audit, Starlink failover monitoring, dedicated account manager.",
        "ideal_for": "Commercial facilities 20+ users",
        "stripe_product": "Already Here LLC — IT Retainer Gold ($699/mo)",
    },
    "drone_retainer": {
        "name": "Drone Survey Retainer — Monthly Portfolio",
        "price_usd": 1500,
        "type": "monthly",
        "description": "3 commercial property surveys/month. Ideal for roofing companies, property managers, solar developers.",
        "ideal_for": "Roofing contractors, property managers, solar installers",
        "stripe_product": "Already Here LLC — Drone Retainer 3x/mo ($1,500/mo)",
    },
}

# ── Monthly recurring revenue projection ─────────────────────────────────────

RETAINER_TARGETS = {
    "month_1": {"bronze": 2, "silver": 1, "gold": 0, "drone": 0},   # $797/mo MRR
    "month_2": {"bronze": 3, "silver": 2, "gold": 0, "drone": 1},   # $3,094/mo MRR
    "month_3": {"bronze": 5, "silver": 3, "gold": 1, "drone": 2},   # $5,692/mo MRR
}

# ── Lead platforms to register on ────────────────────────────────────────────

PLATFORMS = [
    {"name": "Google Business Profile", "url": "business.google.com/create", "cost": "Free", "lead_type": "Inbound search — highest volume", "priority": 1},
    {"name": "Thumbtack Pro",           "url": "thumbtack.com/pro",           "cost": "Pay per lead",  "lead_type": "Active service seekers", "priority": 2},
    {"name": "Bark.com Pro",            "url": "bark.com/en/us/sellers/create", "cost": "Pay per lead","lead_type": "Active service seekers", "priority": 3},
    {"name": "Yelp for Business",       "url": "biz.yelp.com",                "cost": "Free listing", "lead_type": "Local search", "priority": 4},
    {"name": "Nextdoor Business",       "url": "business.nextdoor.com",       "cost": "Free",         "lead_type": "Neighborhood leads", "priority": 5},
    {"name": "Field Nation",            "url": "fieldnation.com",             "cost": "Platform fee", "lead_type": "Dispatch WOs", "priority": 1},
    {"name": "ServiceChannel",          "url": "servicechannel.com/services-providers/get-started", "cost": "Free", "lead_type": "National retail chains", "priority": 2},
    {"name": "Craigslist Phoenix",      "url": "phoenix.craigslist.org",      "cost": "Free",         "lead_type": "Same-day local", "priority": 3},
]

# ── Calendly booking setup instructions ──────────────────────────────────────

CALENDLY_SETUP = """
AUTOMATED BOOKING + PAYMENT — Calendly + Stripe (FREE tier available)
=======================================================================

1. Go to calendly.com → Sign up free
2. Create event types:
   - "Network Audit Booking" — 90 min — $350 — collect payment at booking
   - "Drone Survey Consultation" — 30 min — free (survey priced after scoping)
   - "IT Support Call" — 30 min — $75/hr

3. Connect Stripe (Settings → Billing → Connect Stripe)
   - Payment collected automatically at booking
   - No invoicing, no chasing, no no-shows

4. Share your booking link in every email signature:
   calendly.com/alreadyherellc/audit
   calendly.com/alreadyherellc/drone

5. Add to alreadyherellc.com as "Book Now" button

Result: Clients find you, book themselves, pay themselves. Zero manual work.
"""

# ── Stripe payment link setup ─────────────────────────────────────────────────

STRIPE_SETUP = """
STRIPE PAYMENT LINKS — Zero-code, shareable, works everywhere
=============================================================
Already Here LLC has a Stripe account (set up via SyncroFlow May 2026).

1. Log into dashboard.stripe.com
2. Go to Payment Links → Create
3. Create one link per service:
   - Network Audit: $350 one-time
   - Drone Survey Standard: $750 one-time
   - Drone Survey Premium: $1,200 one-time
   - IT Retainer Bronze: $199/month (recurring)
   - IT Retainer Silver: $399/month (recurring)
   - IT Retainer Gold: $699/month (recurring)
   - Drone Retainer 3x: $1,500/month (recurring)

4. Add your logo + Already Here LLC branding
5. Share links anywhere — email, website, Slack, text

Result: Client clicks link, enters card, pays. Money in your account in 2 days.
The retainer links bill automatically every month. Set it once, collect forever.
"""

if __name__ == "__main__":
    print("\n" + "="*65)
    print("  ALREADY HERE LLC — AUTOMATED REVENUE STREAM SETUP")
    print("="*65)

    print("\n--- SERVICE MENU WITH PRICING ---")
    for key, svc in SERVICES.items():
        price = f"${svc['price_usd']}/mo" if svc["type"] == "monthly" else (f"${svc['price_usd']}" if svc["price_usd"] else "FREE")
        print(f"  {svc['name']:<45} {price}")

    print("\n--- MRR PROJECTION (retainers only) ---")
    for month, mix in RETAINER_TARGETS.items():
        mrr = (mix["bronze"] * 199 + mix["silver"] * 399 +
               mix["gold"] * 699 + mix["drone"] * 1500)
        clients = sum(mix.values())
        print(f"  {month}: {clients} retainer clients = ${mrr:,}/month recurring")

    print("\n--- LEAD PLATFORMS (register in order) ---")
    for p in sorted(PLATFORMS, key=lambda x: x["priority"]):
        print(f"  [{p['priority']}] {p['name']:<25} {p['cost']:<15} {p['lead_type']}")

    print(STRIPE_SETUP)
    print(CALENDLY_SETUP)
