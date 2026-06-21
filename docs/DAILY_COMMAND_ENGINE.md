# Daily Command Engine Production Core

## Review grade

The submitted single-file prototype grades as B-minus for architecture intent and C-plus for production readiness.

It had useful scoring concepts, but it was not production-ready because it used loose raw input typing, random identifiers, unsafe fallback normalization, opportunity revenue as confirmed revenue, and a single try/catch instead of source-level quarantine behavior.

## A-plus implementation standard

The production core must meet these rules:

1. Accept untrusted raw inputs without crashing.
2. Quarantine invalid sources and categories instead of mislabeling them.
3. Use deterministic IDs for auditability.
4. Keep opportunity, bookable, confirmed, invoiced, collected, and disputed value separate.
5. Score field work by route friction and effective hourly value.
6. Block diesel and heavy-duty AutoWorks scope.
7. Require owner approval before external action.
8. Generate a Markdown command export.
9. Expose a read-only API route for approved server-side adapters.
10. Run without embedded private API keys.

## Implemented files

- `lib/daily-command-core.ts`
- `app/api/daily-command/route.ts`
- `app/daily-command/page.tsx`
- `tests/daily-command-core.test.mjs`

## Security model

The core contains no private credentials and performs no network calls. Gmail, GitHub, Calendar, Vercel, Stripe, Square, QuickBooks, Field Nation, and WorkMarket data must enter through approved server-side connectors or explicit JSON feed input.

The engine does not send emails, submit forms, accept work, move money, modify books, deploy production files, or change credentials.

## Revenue model

The engine calculates:

- confirmed revenue
- bookable revenue
- opportunity value
- payment protection exposure
- blocked value
- revenue gap to the 500 dollar daily target

Opportunity value is intentionally not counted as confirmed revenue.

## Approval model

The engine returns approval gates:

- `READ_ONLY`
- `DRAFT_ONLY`
- `OWNER_APPROVAL_REQUIRED`
- `BLOCKED`

The API route is read-only from an execution standpoint. Any future adapter that sends, submits, accepts, pays, or deploys must remain behind explicit Stephen Franklin approval.

## Connector readiness

The implementation is connector-ready, not credential-embedded. That is intentional. Private API keys must not be committed to GitHub. Live credentials belong in Vercel environment variables, OCI secret storage, Bitwarden, or approved connector authorization.
