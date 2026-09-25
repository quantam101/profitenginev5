# MonetizeOS — Agent Operations

## Running

```bash
export PYTHONPATH=.
python scripts/monetizeos.py init <project_id> --name "Project"
python scripts/monetizeos.py audit <project_id> --repo-root . --artifact-dir artifacts/
python scripts/monetizeos.py enqueue <project_id> contract.json [--priority 50]
python scripts/monetizeos.py run <project_id> --worker worker-1 --repo-root .
python scripts/monetizeos.py status <project_id>     # Lifelong Catch and Correct view
python scripts/monetizeos.py cancel <project_id> <task_id>
python scripts/monetizeos.py gates <project_id>
python scripts/monetizeos.py gate-pass <project_id> <gate> --evidence '{"passed":true,...}'
```

State lives in `data/monetizeos.db` (override with `--db` or `MONETIZEOS_DB`).

## Continuous operation

The CLI is stateless — one `run` invocation drains currently-schedulable
work. Recurring work requires a configured scheduler; nothing pretends
to run after the process exits. Options:

- cron: `*/5 * * * * cd repo && PYTHONPATH=. python scripts/monetizeos.py run <project>`
- systemd timer, or a GitHub Actions cron workflow calling the same command.
- Long-running workers: wrap `run` in a supervisor that re-invokes it;
  the Director lease renews each cycle, so a crashed worker's lease
  simply expires and a new one fences it out.

## Pause / resume / cancel / rollback

- **Cancel a task**: `cancel` sets `cancel_requested` (a running worker
  can poll `store.cancel_requested`) and moves it to `cancelled`.
- **Pause the Director**: stop invoking `run`. The lease expires
  (default 60s); resume by invoking `run` again — `acquire()` re-fences.
- **Rollback**: state is append-mostly; reverse a bad completed task by
  recording a corrective task + decision (`record_decision`) — decisions
  and changelog are immutable audit records, not rewritten history.
- **Recover**: on restart, `claim()` sweeps expired worker leases back to
  schedulable. Attempts, reports, artifacts and incidents all survive.

## Incidents

Dead-lettered tasks and handler exceptions land in `incidents`
(`status` surfaces `open_incidents`). Inspect directly:
`sqlite3 data/monetizeos.db "SELECT * FROM incidents WHERE status='open'"`.

## Cost policy

Zero-spend default (`budget_usd` defaults to 0.0, consistent with
`max_cost_usd: 0` repo policy). All consumption is recorded per task in
`cost_events` (tokens, usd, duration via attempts). Deterministic work
(validation, transitions, checksums) is code, not model calls; specialist
handlers that use AI must record `tokens_used`/`cost_usd` in their
CompletionReport — unreported consumption is treated as zero but visible
as such in `status`.

## Security rules enforced by the runtime

- Role permission sets checked at delegation (`check_permissions`).
- No handler ⇒ fail closed + incident; never simulate an agent.
- Secrets are never written to contracts, reports, decisions or the
  changelog — pass credential *names*, resolve at runtime.
- Director cannot pass a mandatory-evidence gate without a passing
  evidence record (`MANDATORY_EVIDENCE_GATES`), and cannot mark a failed
  check passed — `gate-pass` refuses `{"passed": false}` evidence.
- `live_payment_verified` rejects `test_transaction` evidence.

## Registering specialist handlers

Handlers are Python callables `(contract, ctx) -> CompletionReport`
registered on `Director.handlers[role]`. `command_check_handler(cmd)`
wraps any deterministic check (pytest, scripts/security-check.sh).
Specialists needing judgment should call the local inference cascade
(`runtime/inference_cascade.py` / Ollama) to stay inside the zero-spend
boundary, and record actual usage in the report.
