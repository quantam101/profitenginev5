# Revenue OS Seed Data v1

This dataset preserves the first 65 Already Here LLC revenue plays as version-controlled seed data.

## Files

- `data/revenue-os/revenue-plays.seed.json` — normalized records RP-001 through RP-065.
- `scripts/validate-revenue-os-seed.mjs` — structural, duplicate-ID, count, and score validation.

## Safety policy

The dataset is research and planning data only. It does not authorize outreach, public posting, account creation, spending, form submission, vendor registration, pricing commitments, or contractual commitments.

## Validation

Run:

```bash
node scripts/validate-revenue-os-seed.mjs
```

Expected output:

```text
Validated 65 Revenue OS seed records.
```

## Import contract

The future Revenue OS importer should:

1. Validate this file before database writes.
2. Upsert by immutable `id`.
3. Preserve source and notes.
4. Recalculate opportunity scores using the active scoring-engine version.
5. Add created/updated timestamps and audit events.
6. Keep every record in `SEED_READY` until target-company enrichment and owner approval.
7. Prevent all outbound actions unless a separate explicit approval event exists.

## Current limitation

These 65 records are normalized strategic revenue-play records, not verified individual company or contact records. Target companies, public vendor-management paths, source URLs, and contacts must be researched, verified, deduplicated, and linked separately before activation.
