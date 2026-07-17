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

- **Checkout/delivery: Gumroad** (hosting, secure delivery, receipts for ~10%).
  Stripe Payment Links + webhook fulfillment saves ~7% in fees but requires a
  delivery server (expiring links) we deliberately don't run. Revisit when
  gross passes ~$2k/mo — then the fee delta funds the Render backend work.
- **Orchestration: GitHub Actions**, not n8n — no server to keep alive, free
  minutes cover the whole pipeline, fail-soft steps already proven.
- **Writing: our own production experience** — never bulk LLM generation
  (`max_cost_usd: 0` is a hard project constraint, and generic AI books
  can't hold a $30 price).
- **Rendering: make_ebook.py** (HTML/CSS → headless-Edge PDF), $0, no
  WeasyPrint/GTK dependency chain.
- **Post-purchase nurture: Beehiiv via gumroad_buyers_to_beehiiv.py** in the
  daily revenue workflow; the Monday newsletter is the drip.
