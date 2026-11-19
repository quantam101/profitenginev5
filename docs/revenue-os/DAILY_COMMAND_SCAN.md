# Daily Command revenue scan feed

`POST https://app.alreadyherellc.com/api/revenue-os/daily-command-scan`

Read-only feed that Daily Command OS's scheduled **Revenue opportunity scan** calls. It never
generates synthetic opportunities: every event comes from Revenue OS data.

## Auth

- `Authorization: Bearer <PROFITENGINE_WEBHOOK_TOKEN>` or `x-profitengine-token: <PROFITENGINE_WEBHOOK_TOKEN>`
- `503` when `PROFITENGINE_WEBHOOK_TOKEN` is not configured, `401` on a missing/wrong token.
- Send a non-bot `User-Agent` (the edge middleware returns `403` for `curl`, `wget`, `python-requests`, ...).

## Request body (optional JSON)

| field | default | range |
|---|---|---|
| `limit` | 10 | 1–50 |
| `min_score` | 50 | 0–100 (Revenue OS `overallScore`) |

## Sources, in order

1. Active Revenue OS pipeline opportunities in MongoDB (`opportunities`, stage not Won/Lost/On Hold),
   joined with their company and revenue play, sorted by `weightedValue`.
2. Revenue plays (`revenue_plays`, status SEED_READY/RESEARCH/ACTIVE) with `overallScore >= min_score`.
   If MongoDB is not configured, unreachable, or has no revenue plays, the committed catalog
   `data/revenue-os/revenue-plays.seed.json` is used and a `warnings` entry explains why.

## Response

```json
{
  "ok": true,
  "status": "completed",
  "scanned_at": "2026-11-10T16:00:00.000Z",
  "limit": 10,
  "min_score": 50,
  "sources": { "pipeline_opportunities": 0, "revenue_plays_considered": 65, "revenue_plays_emitted": 10, "revenue_play_source": "seed_catalog" },
  "warnings": [],
  "event_count": 10,
  "events": [
    {
      "event_type": "revenue_opportunity.detected",
      "source": "profitenginev5.revenue-os",
      "idempotency_key": "revenue-os:play:RP-001",
      "data": { "company": "...", "grade": "C", "external_id": "revenue-os:play:RP-001" }
    }
  ]
}
```

Each event matches Daily Command's `OpportunityDetected` schema; empty fields are omitted (Daily Command
rejects `null`). `external_id` is stable (`revenue-os:opportunity:<_id>` or `revenue-os:play:<recordId>`),
so repeated scans upsert instead of duplicating. Daily Command signs and forwards each event to its own
`/api/events/webhook`; outreach still requires human approval there.
