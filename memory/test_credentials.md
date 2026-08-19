# Test credentials

ProfitEngine v5 currently has **no authentication** — all endpoints are open.
This is intentional during closed beta.

## API

| Endpoint | Auth |
| --- | --- |
| `/api/*` | none |

## Mongo

| Setting | Value |
| --- | --- |
| URL | `mongodb://127.0.0.1:27017` (from `/app/backend/.env`) |
| DB | `profitengine` |

When auth is introduced (Holding tier — SSO + audit log), credentials will be
documented here.
