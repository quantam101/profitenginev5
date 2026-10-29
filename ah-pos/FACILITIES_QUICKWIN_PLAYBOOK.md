# Facilities Quick-Win Playbook (AH-POS)

Source idea: a short-form video pitching "position your company as a facilities support contractor — 4 contracts at $25,000 = $100,000," winning on response time and pricing. This doc turns that into rules that hold up under current regulations, wired to `backend/facilities_quickwin.py`.

## Why the math works

- **Thresholds (FAR 2.101, effective 2025-10-01):** micro-purchase threshold $15,000; simplified acquisition threshold (SAT) $350,000.
- **Under $15K:** buyers can use a purchase card with little or no competition. You win these by being known to the buyer, not by bidding.
- **$15K–$350K:** simplified acquisition (FAR Part 13): short RFQs, fast awards, and the work is generally reserved for small business when two or more capable small firms are expected to bid.
- **A $25K job sits in the sweet spot:** small enough that big primes ignore it, large enough to be worth a truck roll.
- **Funnel math:** 4 wins needs about 20 bids at a 20% win rate. The scanner prints this every run (`--goal`, `--avg-award`, `--win-rate`).

## NAICS to register in SAM.gov

| Tier | NAICS | Work |
|---|---|---|
| Primary | 561210 | Facilities support (bundled maintenance/janitorial/O&M) |
| Core | 561720, 561730, 561790 | Janitorial, landscaping, building services |
| Core | 238210, 238220 | Electrical, HVAC/plumbing |
| Core | 811310, 811210 | Equipment repair (incl. commercial kitchen and appliance), electronics |
| Adjacent | 541512, 541519, 238290, 238990, 236220, 561990 | IT field services, specialty trades |

The 561210 size standard is about $47M in average receipts, so Already Here is comfortably small. Confirm against the current SBA size table before certifying.

## Daily operating loop

1. **06:05 Phoenix, weekdays:** the scan runs (`.github/workflows/ah-pos-facilities-scan.yml`), then posts the digest to Telegram and the Actions summary.
2. **Bid the top items the same day.** Response time is the edge. Combined synopsis/solicitations (`k`) are the classic quick-turn RFQs.
3. **Answer every Sources Sought (`r`) in your NAICS.** It costs nothing, and it is how a contracting officer learns two small firms exist, which is what triggers a set-aside.
4. **Weekly: work the "repeat buyers" list.** Send each office a one-page capability statement and ask the contracting officer about upcoming small buys and purchase-card work under $15K.
5. **Log every award in the past-performance DB** (`ingest_past_performance.py`). Each small win makes the next bid stronger.

## Pricing rules that keep you profitable

- **Service Contract Act:** most services contracts over $2,500 carry a wage determination. Price janitorial and maintenance labor at or above the WD rate plus fringe, or the bid is non-compliant.
- **Build price from the AH-POS pricing engine:** loaded labor, travel, materials, insurance and G&A, then margin. Never price by guessing the incumbent's number.
- **Cheapest isn't automatic:** most RFQs at this size are lowest-price-technically-acceptable, so "acceptable" (complete forms, licenses, insurance certificates) matters as much as price.

## Eligibility guardrail

The scanner treats only open small-business (`SBA`, `SBP`) and unrestricted notices as biddable. SDVOSB, WOSB, HUBZone and 8(a) set-asides are excluded unless the cert code is listed in the `AH_POS_CERTS` repo variable. Never bid a set-aside you don't hold; misrepresenting status is a False Claims Act exposure.

## Setup

1. Make sure SAM.gov entity registration is **Active** with the NAICS above.
2. Generate a key at SAM.gov > Account Details > Public API Key. Add it as repo secret `SAM_GOV_API_KEY`.
3. Optional repo variables:
   - `AH_POS_STATES` (default `AZ`; e.g. `AZ,NV,NM`)
   - `AH_POS_CERTS`
   - `SAM_MAX_CALLS` (default 6; public keys have a small daily quota)
4. Run manually: Actions > AH-POS Facilities Quick-Win Scan > Run workflow.

Local run:

```
SAM_GOV_API_KEY=... python ah-pos/backend/facilities_quickwin.py --days-back 3 --award-days 90
```
