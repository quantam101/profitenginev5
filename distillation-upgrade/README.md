# Data Distillation Upgrade — ProfitEngine v5.x
**Already Here LLC** | alreadyhereillc.com

## What this adds

The existing `core/distillation.js` achieves ~40% token reduction via prompt minification and MD5 dedup. This upgrade implements all 5 pillars of the full Data Distillation strategy, targeting **70-85% total reduction** on large inputs with **zero change** to existing `distillation.js` or `sovereign.js`.

---

## Files

| File | Pillar | What it does |
|---|---|---|
| `core/semantic-compressor.js` | 1 | HTML strip → chunk (512 tok) → cosine RAG → top-4 chunks |
| `core/tiered-router.js` | 2, 3, 5 | LOW/MID/HIGH routing · YAML/JSON/pipe serializer · few-shot builder · output constraints |
| `core/logic-offloader.js` | 4 | Deterministic offload: sort, dedupe, math, extract, format |
| `pipeline/distillation-pipeline.js` | all | Orchestrator — wires all pillars + existing distillation.js |
| `pipeline/integration-patch.js` | — | Drop-in patches for each agent call site |
| `config/distillation.yaml` | — | Single declarative config for all 5 pillars |

---

## Pipeline flow

```
raw input
  │
  ▼ Pillar 4 — logic-offloader: sort/dedupe/math/extract → return immediately (0 tokens)
  │
  ▼ Pillar 1 — semantic-compressor: HTML strip → RAG → top-4 chunks (~70% reduction on docs)
  │
  ▼ Pillar 5 — tiered-router: complexity score → LOW/MID/HIGH tier + model selection
  │
  ▼ Pillar 2 — prompt engineering: output constraints + few-shot density
  │
  ▼ existing distillation.js: distillPHPrompt + dedup cache + budget gate (existing ~40%)
  │
  ▼ Pillar 3 — structural serialization: YAML (LOW/MID) or compact JSON (HIGH)
  │
  ▼ LLM call (caller responsibility)
  │
  ▼ Pillar 4 post-process: cleanResponse → strip filler → extract JSON/YAML
  │
  ▼ commitResponse → dedup cache → future identical prompts = $0.00
```

---

## Tier map

| Tier | Complexity | Model | Cost/1K tok | Use case |
|---|---|---|---|---|
| LOW | ≤ 0.20 | none (code) | $0.0000 | sort, math, dedupe, format |
| MID | ≤ 0.55 | gemma2-9b-it | $0.0001 | summarize, extract, classify, SEO |
| HIGH | > 0.55 | llama-3.3-70b | $0.0009 | strategy, generation, reasoning |

---

## Integration — minimal diff per agent

```js
// BEFORE (any agent)
const response = await llm.generate(rawContent);

// AFTER (full 5-pillar pipeline)
const dp   = require('./pipeline/distillation-pipeline');
const prep = await dp.prepare(rawContent, { taskType: 'summarize', query: topic });
if (prep.fromCache)      return prep.cachedResponse;   // dedup hit — $0.00
if (prep.offloaded)      return prep.offloadResult;    // code handled it — $0.00
if (prep.budgetExceeded) return null;                  // daily limit
const raw  = await llm.generate(prep.prompt, prep.routing);
const resp = dp.finalize(raw, prep, { extractJSON: true });
return resp.text;
```

Pre-built integration for every agent is in `pipeline/integration-patch.js`:
- `trendScannerPrepare()` — scrape compress + extract
- `contentGeneratorPrepare()` — RAG over trend report
- `seoAgentPrepare()` — MID tier, YAML schema
- `complianceCheck()` — pure regex, zero tokens
- `revenueAggregation()` — pure math/sort, zero tokens
- `lccStrategyPrepare()` — HIGH tier, YAML state serialization
- `procurementScanPrepare()` — BOS Agent C integration

---

## Expected savings

| Scenario | Before | After | Saving |
|---|---|---|---|
| Short prompt (< 600 tok) | distillPHPrompt: ~40% | same + filler strip | ~42% |
| Large doc / log (> 2000 tok) | full doc sent | RAG top-4 chunks | ~75% |
| Repeat prompt | LLM call | cache hit | 100% |
| Sort / math / dedupe | LLM call | code offload | 100% |
| SEO extraction | llama-70b | gemma2-9b | ~90% cost reduction |
| Config payload | JSON | YAML | ~20% tokens |

---

## Status endpoint

After wiring `pipeline/integration-patch.getPipelineStatusSection()` into `api/routes/status.js`:

```
GET /api/status.distillation   → existing distillation.js stats
GET /api/status.compressor     → RAG chunks indexed, top-K hits
GET /api/status.tierRouter     → cost by tier, total USD spent
GET /api/status.offloader      → tasks offloaded, tokens saved
GET /api/status.sovereign      → Redis availability, semantic cache
```

---

## Environment variables

```bash
# Pillar 1
COMPRESSOR_ENABLED=true
COMPRESSOR_CHUNK_TOKENS=512
COMPRESSOR_OVERLAP_TOKENS=64
COMPRESSOR_TOP_K=4

# Pillar 5
TIER_THRESHOLD_LOW=0.20
TIER_THRESHOLD_MID=0.55
TIER_MID_MODEL=gemma2-9b-it
TIER_MID_MAX_TOKENS=512

# Pipeline
MAX_INPUT_TOKENS=3000
DAILY_TOKEN_LIMIT=500000

# Existing (unchanged)
DISTILL_ENABLED=true
QWEN_ENABLED=false
ENTERPRISE_REDIS_HOST=127.0.0.1
```

---

## Deploy to OCI (profitengine-server 152.70.150.68)

```bash
# Copy new files alongside existing core/
cp core/semantic-compressor.js  ~/profitengine/core/
cp core/tiered-router.js        ~/profitengine/core/
cp core/logic-offloader.js      ~/profitengine/core/
cp pipeline/distillation-pipeline.js ~/profitengine/pipeline/
cp pipeline/integration-patch.js     ~/profitengine/pipeline/
cp config/distillation.yaml          ~/profitengine/config/

# No new npm dependencies — uses only Node.js built-ins (crypto, fs)
# Restart PM2
pm2 restart profitengine
pm2 logs profitengine --lines 30
```
