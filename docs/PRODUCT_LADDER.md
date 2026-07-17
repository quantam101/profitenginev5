# Product Ladder & Validation Gates

Roadmap for the digital-product side of the funnel. Rule #1, from hard-won
consensus: **one excellent product, validated, before the next is built.**
Unvalidated ebooks are inventory, not revenue.

## Live ladder (content niche)

| # | Product | Price | Status |
|---|---------|-------|--------|
| 0 | The $0 Content Engine (free edition) | $0 — lead magnet | LIVE — GitHub Pages, linked in every video description |
| 1 | The $0 Content Engine: Complete Blueprint | $30 | BUILT — PDF ready; sales page live at quantam101.github.io/content/ebooks/blueprint/; **waiting on manual Gumroad product creation** |

## Queued ladder (field-service niche — real domain authority via dispatch ops)

| # | Product | Price | Gate to start building |
|---|---------|-------|------------------------|
| 2 | Field Technician Profit & Protection System (ebook + intake form, condition/photo checklists, scope-change authorization, pricing calculator, closeout + sign-off templates, invoice follow-up scripts) | $30 | Product #1 has ≥10 total sales OR ≥30 days live with traffic data to learn from |
| 2a | Free site-visit checklist (lead magnet for #2) | $0 | Built alongside #2 |
| 3 | Complete editable forms bundle | $49 | #2 converting; offered as upsell |
| 4 | Small Field-Service Business Operating System | $99 | #3 selling; premium bundle |
| 5 | Implementation consultation | $250+ | Inbound demand observed (dispatch@ replies) |

Core promise for the field-service line: *document every job, prevent
disputes, price work correctly, get paid faster.* Outcome, not information —
that's what justifies the price.

## Optimization gates (do not tinker below these thresholds)

- No copy/price/cover changes on fewer than ~100 sales-page sessions or 10 sales per variant
- Kill a promo angle only after ≥5 posts with below-median engagement
- New edition of a product only from recurring buyer questions, not one-offs

## Infrastructure decisions of record

- **Checkout/delivery: Gumroad now, Stripe later — two-channel plan.**
  Phase 1 (now): Gumroad is launch + delivery + merchant of record for ~10%.
  Phase 3 (gated): Stripe Managed Payments storefront on an owned domain
  (e.g. products.alreadyherellc.com) as the permanent API-first store —
  products/prices/payment-links created programmatically, webhook fulfillment
  with expiring download links, Gumroad demoted to secondary marketplace.
  **Gates before Phase 3 starts:** (1) first product validated on Gumroad
  (≥10 sales or ~$2k/mo gross in sight — the fee delta funds the build),
  (2) Stripe keys rotated first (see SECURITY_ROTATION_REQUIRED.md — the
  current secret key was in the exposed .env), (3) Managed Payments
  eligibility/pricing confirmed inside the Stripe dashboard, (4) delivery
  service lands on the existing Render backend, not new infrastructure.
  Never a Gumroad browser-robot: no stable API underneath, breaks on UI
  changes, and a half-published product is worse than a manual step.
- **Orchestration: GitHub Actions**, not n8n — no server to keep alive, free
  minutes cover the whole pipeline, fail-soft steps already proven.
- **Writing: our own production experience** — never bulk LLM generation
  (`max_cost_usd: 0` is a hard project constraint, and generic AI books
  can't hold a $30 price).
- **Rendering: make_ebook.py** (HTML/CSS → headless-Edge PDF), $0, no
  WeasyPrint/GTK dependency chain.
- **Post-purchase nurture: Beehiiv via gumroad_buyers_to_beehiiv.py** in the
  daily revenue workflow; the Monday newsletter is the drip.
