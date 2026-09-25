# MonetizeOS — Optimization Baseline

Recorded 2026-09-25 against the profitenginev5 working tree (branch
`devin/…-monetizeos`). "Maximum optimization" means measurable change
against this baseline — no claim of perfect optimization, guaranteed
revenue, or capability beyond what is demonstrated.

## Repository baseline (measured)

| Metric | Value | Method |
|---|---|---|
| Files (excl. .git, node_modules) | 1,921 | `find` walk (repository_auditor handler) |
| Python LOC | 48,710 | `find -name '*.py' | xargs cat | wc -l` |
| Test files | 17 | `ls tests/test_*.py tests/taylor/test_*.py` |
| Pytest cases collected | 203 | `pytest --collect-only` (before this change) |
| MonetizeOS tests added | 22 | `tests/test_monetizeos.py` |
| Lint scope (CI ruff) | backend, code_merger, scripts/seo_content_quality.py, tests/test_seo_content_quality.py | `ci.yml` |
| Paid-spend ceiling | $0 (`max_cost_usd: 0`) | repo policy, enforced by CostGuard + contract budgets |

## Commercial hypothesis (from repo audit)

The repo already contains: LLM gateway cascade with a $0 local tier
(`inference_cascade`, Ollama gateways), content-generation engines
(city_seo_engine, revenue OS integration via `fye.job_event` →
daily-command-os), an approval control plane, and the FYE render
pipeline. The strongest near-term monetizable capability is
**orchestrated, approval-gated content/dispatch pipelines** — the pieces
exist; what was missing is the durable supervisor/specialist control
plane this change adds. Buyer: the operator of Already Here LLC
(internal first customer); external productization is a later gate.

## Execution baseline

| Metric | Baseline | Target |
|---|---|---|
| Durable task orchestration | none (ad-hoc scripts, JSONL logs) | SQLite WAL store, transactional lifecycle |
| Supervisor safety | none | lease + fencing token, failover-tested |
| Idempotent task delivery | none | UNIQUE idempotency keys + outbox dedupe |
| Retry handling | none | bounded backoff+jitter, dead-letter incidents |
| Release gating | none | 10 ordered gates + 6 revenue milestones |
| Cost accounting per task | none | cost_events (tokens, usd, duration) |
| Cancellation | none | cancel_requested flag + cancelled state |

## Measurement going forward

`monetizeos.py status` reports: tasks by state, attempts, average
attempt duration, tokens, USD, open incidents, pending outbox, next
gate. Each retained/rolled-back improvement must cite these numbers in
its improvement proposal (improvement_engineer output format:
evidence → bounded change → regression checks → measured delta vs this
baseline).
