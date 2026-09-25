# MonetizeOS — Agent Architecture

One supervisory AI (the **Director**) plus one accountable **specialist**
per process, coordinated through a durable SQLite store — not through
conversation state.  `runtime/monetizeos/` is the runtime; role prompts
or config files alone are not the system.

## Topology

```
                ┌────────────────────────────┐
                │        Director            │  1 per project
                │  lease + fencing token     │  (renewable, fenced)
                └─────────────┬──────────────┘
                              │ delegates TaskContracts
              ┌───────────────┼─────────────────┐
              ▼               ▼                 ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │ Specialist A │ │ Specialist B │ │ Specialist … │  1 per process
      │ (bounded)    │ │ (bounded)    │ │ (bounded)    │  activated on demand
      └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
             └────────────────┴────────────────┘
                              │ CompletionReports + artifacts
                              ▼
                 ┌─────────────────────────┐
                 │   Store (SQLite / WAL)   │
                 │ projects · tasks · edges │
                 │ leases · attempts ·      │
                 │ artifacts · decisions ·  │
                 │ outbox · costs ·         │
                 │ incidents · changelog    │
                 └─────────────────────────┘
```

## Components

| Module | Role |
|---|---|
| `runtime/monetizeos/store.py` | Durable state. WAL SQLite; every mutation inside `BEGIN IMMEDIATE`/`COMMIT`. Director lease + fencing token; worker leases swept on claim; outbox dedupe. |
| `runtime/monetizeos/states.py` | Legal lifecycle graph: `pending → ready → running → verifying → completed`, plus `blocked / retry_wait / failed / cancelled`. Illegal transitions raise. |
| `runtime/monetizeos/contracts.py` | `TaskContract` (objective, inputs+versions, deps, allowed files/tools/actions, outputs, acceptance criteria, verification method, budgets, retry limit, escalation, idempotency key) and `CompletionReport` (status, artifacts, files changed, tests run+results, assumptions, risks, consumption). |
| `runtime/monetizeos/director.py` | Baseline, dependency graph, delegation, permission checks, scheduling (`run_once`), verification, escalation. One live Director per project enforced by `directors` table. |
| `runtime/monetizeos/specialists.py` | Registry of the 15 process roles with minimum-permission sets; deterministic built-in handlers (`repository_auditor`, `command_check_handler`). Roles without a registered handler fail closed — the runtime never pretends an agent ran. |
| `runtime/monetizeos/gates.py` | Ordered release gates (10) and revenue milestones (6). Mandatory-evidence gates cannot be passed without `{"passed": true}` evidence; test transactions never count as revenue. |
| `scripts/monetizeos.py` | CLI: `init / audit / enqueue / run / status / cancel / gates / gate-pass`. `status` renders the Lifelong Catch and Correct view. |

## One Director, enforced

`directors(project_id PRIMARY KEY, holder, fencing, lease_expires_at)`.
Acquiring the lease increments `fencing`. Every Director-issued mutation
re-validates the fencing token inside the same transaction — a stale or
crashed supervisor cannot issue work after failover
(`test_failover_after_lease_expiry_and_stale_fencing_rejected`).

## One specialist per process, enforced

`TaskContract.process_owner` must be one of `SPECIALIST_ROLES`. The
contract's `allowed_tools`/`external_actions` are checked against the
role's permission set at `delegate()` time; violations escalate instead
of running. Specialists never spawn agents — only the Director creates
tasks, so no uncontrolled recursion exists.

## Parallelism

Concurrency is bounded by data, not declarations: one active lease per
`task_id` (single `UPDATE ... WHERE state='ready'` claim), dependency
edges gate scheduling, and callers isolate file ownership via
`allowed_files` in the contract. When no handler or worker is available,
the task stays queued — the runtime never fabricates progress.

## Delivery semantics

Task delivery is at-least-once: `tasks.idempotency_key` is UNIQUE
(same key + same payload → same task; same key + different payload →
`DuplicateIdempotencyKey`). Side effects go through the durable
`outbox` with `dedupe_key UNIQUE` — emit() is idempotent, delivery
marks `delivered_at`.

## Failure model

Bounded retries with exponential backoff + jitter (`2**attempt` capped
60s). Exhausted retries → `failed` + `dead_letter` incident + dependents
`blocked`. Worker death → lease expiry → `retry_wait` → `ready`.
Cancellation sets `cancel_requested` (observable by the worker) then
transitions to `cancelled`.
