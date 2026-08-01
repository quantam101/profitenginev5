---
name: Testing Revenue OS CRM end-to-end
description: How to set up and run an authenticated local end-to-end test of the Revenue OS CRM, AI Advisor, and Integrations in profitenginev5.
---

# Testing Revenue OS CRM end-to-end

## Preconditions

- A local MongoDB instance on `127.0.0.1:27017` with a `profitengine` database.
- The repo is on the branch being tested and dependencies are installed (`npm install`).
- `REVENUE_OS_ENABLED=true` is required for `/revenue-os` pages and `/api/revenue-os/*` routes to be mounted.

## Required environment variables for `npm run dev`

```bash
MONGODB_URI="mongodb://127.0.0.1:27017/profitengine"
NEXTAUTH_SECRET="dev-secret-for-local-test-only"
GOOGLE_CLIENT_ID="local-test.google-client-id"
GOOGLE_CLIENT_SECRET="local-test.google-client-secret"
REVENUE_OS_ENABLED=true
# For the AI Advisor and Integrations smoke tests:
REVENUE_OS_AI_ENABLED=true
GMAOS_LOCAL_MODEL_ENABLED=false   # forces template fallback; avoids calling Ollama
REVENUE_OS_SLACK_ENABLED=false    # keep disabled to avoid outbound Slack webhook calls
REVENUE_OS_ZAPIER_ENABLED=false   # keep disabled to avoid outbound Zapier webhook calls
```

## Start the dev server

```bash
cd /home/ubuntu/repos/profitenginev5
MONGODB_URI="mongodb://127.0.0.1:27017/profitengine" \
NEXTAUTH_SECRET="dev-secret-for-local-test-only" \
GOOGLE_CLIENT_ID="local-test.google-client-id" \
GOOGLE_CLIENT_SECRET="local-test.google-client-secret" \
REVENUE_OS_ENABLED=true \
REVENUE_OS_AI_ENABLED=true \
GMAOS_LOCAL_MODEL_ENABLED=false \
REVENUE_OS_SLACK_ENABLED=false \
REVENUE_OS_ZAPIER_ENABLED=false \
npx next dev -p 3000
```

Wait for `Ready in ...` in the log.

## Authenticating without Google OAuth

Google OAuth cannot be completed in an automated browser, so create an encrypted NextAuth JWT and set it as a cookie.

### 1. Generate the token

Create a small script (do not commit it):

```javascript
// /tmp/make-token.mjs
import { encode } from 'next-auth/jwt';
const token = await encode({
  token: { name: 'Devin Test', sub: 'devin-test-1' },
  secret: 'dev-secret-for-local-test-only',
});
console.log(token);
```

Run it:

```bash
cd /home/ubuntu/repos/profitenginev5
node /tmp/make-token.mjs
```

### 2. Set the cookie in Chrome

Open `http://localhost:3000/revenue-os`, then in the browser console run:

```javascript
document.cookie = `next-auth.session-token=<TOKEN_FROM_SCRIPT>;path=/;SameSite=Lax`;
location.reload();
```

The cookie name is `next-auth.session-token` when `NEXTAUTH_URL` is not HTTPS.

## Typical end-to-end checks

1. Load `/revenue-os` and verify dashboard summary numbers are `0` before creating data.
2. Create a company and contact via API or the UI forms on `/revenue-os/companies` and `/revenue-os/contacts`.
3. Create an opportunity on `/revenue-os/opportunities`, advance it through the pipeline, and confirm:
   - The card updates to the next stage.
   - Follow-ups are generated on `/revenue-os/follow-ups` (notably `Outreach Approved` creates a due-today task).
   - A `Negotiation` opportunity can be advanced all the way to `Won`.
4. Complete a follow-up and confirm the dashboard summary updates.
5. Open `/revenue-os/ai` and verify:
   - Top recommended opportunities are ranked.
   - Data-quality flags appear for incomplete records.
   - Draft generator (Intro Email, etc.) produces a draft and can save it.
   - Approval queue transitions: Draft → Needs Review → Approved → Executed.
6. Open `/revenue-os/integrations` and verify:
   - Slack and Zapier are shown as disabled.
   - Send/Dispatch buttons are disabled.
   - Delivery Log and Slack Log are empty until a logged-but-disabled dispatch is created.
7. Test negative cases with `curl`:
   - `GET /api/revenue-os/dashboard/summary` without the cookie → `401 Unauthorized`.
   - `GET /api/revenue-os/dashboard/summary` with `REVENUE_OS_ENABLED=false` → `404 Revenue OS is not enabled`.
8. Run `npm run lint`, `npm run typecheck`, `npm run security:scan`, and `MONGODB_DB=revenue-os-test npm run test:revenue-os`.

## Automated test run

```bash
cd /home/ubuntu/repos/profitenginev5
MONGODB_DB=revenue-os-test MONGODB_URI="mongodb://127.0.0.1:27017/profitengine" \
  npm run test:revenue-os
```

`MONGODB_DB` is honored by `lib/mongodb.mjs` and keeps the integration tests from overwriting the `profitengine` dev database.

## Notes

- The `Create Opportunity` form uses a native `<button type="submit">`. Some automation click tools emit `pointerdown`/`pointerup` without a native `click` event, so the form may not submit. If this happens, use `document.querySelector('form button[type=submit]').click()` or `document.querySelector('form').requestSubmit()` from the console as a workaround. The `Advance`, `Complete`, and AI Advisor queue buttons have explicit React `onClick` handlers and generally respond to automation clicks; if a queue button does not fire, `button.click()` from the console is a reliable fallback.
- `lib/mongodb.mjs` derives the database name from `MONGODB_DB`/`DB_NAME` first, then from the database segment in `MONGODB_URI`, and finally falls back to `profitengine`.
- `GMAOS_LOCAL_MODEL_ENABLED=false` forces `ai-advisor.mjs` to use its local template fallback, so no network call is made to Ollama.
- When Slack/Zapier are disabled (no webhook URL or secret), the adapter services persist a local `SKIPPED`/`DISABLED` log record and do not perform an outbound `fetch`.
- If `npm run build` is run while `next dev` is serving, delete the `.next` directory before restarting `next dev` to avoid stale/missing server chunks.
- Revenue play seed data comes from the existing `revenue_plays` collection; keep it intact or re-seed if cleared.

## Devin Secrets Needed

- `NEXTAUTH_SECRET`: for generating the local `next-auth.session-token`.
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: local-test values are acceptable for local dev; real values are only needed for actual OAuth sign-in.
