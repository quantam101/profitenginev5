# Revenue OS Seed Data v1

## Scope

This seed package contains 90 sequential Revenue OS opportunity records:

- `RP-001` through `RP-065` in `data/revenue-os/revenue-plays.seed.json`
- `RP-066` through `RP-070` in `data/revenue-os/revenue-plays.seed.v1.2.json`
- `RP-071` through `RP-075` in `data/revenue-os/revenue-plays.seed.v1.1.json`
- `RP-076` through `RP-080` in `data/revenue-os/revenue-plays.seed.v1.4.json`
- `RP-081` through `RP-085` in `data/revenue-os/revenue-plays.seed.v1.3.json`
- `RP-086` through `RP-090` in `data/revenue-os/revenue-plays.seed.v1.5.json`

The records are version-controlled strategy and research data. They are not verified company or contact records.

## Validation

Run:

```bash
npm run validate:revenue-os
```

Validation requires:

- exactly 90 records across all datasets;
- sequential IDs from `RP-001` through `RP-090`;
- no duplicates;
- all required fields;
- opportunity score equal to the sum of score inputs.

## MongoDB dry run

```bash
npm run revenue-os:seed:dry-run
```

The dry run requires `MONGODB_URI` and reports existing and potential new records without modifying MongoDB.

## MongoDB import

```bash
npm run revenue-os:seed
```

Default database: `profitenginev5`  
Default collection: `revenue_plays`

The importer:

- loads all six datasets;
- rejects duplicate or missing sequential IDs;
- creates required indexes;
- performs idempotent upserts by `id`;
- preserves `created_at` and `manual_overrides` on existing records;
- writes an audit event to `revenue_os_audit_events`.

The protected administrative API endpoint applies the same six-dataset, 90-record, sequential-ID validation before any write.

## Environment variables

```text
MONGODB_URI
MONGODB_DB
REVENUE_OS_COLLECTION
REVENUE_OS_IMPORT_ACTOR
REVENUE_OS_IMPORT_SECRET
```

Only `MONGODB_URI` is required for the command-line importer. `REVENUE_OS_IMPORT_SECRET` protects the administrative HTTP import endpoint.

## Safety boundary

Seed import does not authorize outreach, posting, account creation, registration, spending, form submission, pricing changes, contract acceptance, or any external commitment. All external actions remain approval-gated.
