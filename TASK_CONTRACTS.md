# MonetizeOS — Task Contracts

Every delegated unit of work is a `TaskContract`
(`runtime/monetizeos/contracts.py`). Every completion is a
`CompletionReport`. A bare declaration of success is not accepted as
evidence — a `completed` report must record the tests that actually ran
and every one must have `result == "passed"`.

## TaskContract fields

| Field | Required | Meaning |
|---|---|---|
| `task_id` | yes | Unique task identifier. |
| `process_owner` | yes | One of the 15 `SPECIALIST_ROLES` — the accountable process. |
| `objective` | yes | What the task does. |
| `business_purpose` | yes | Why it exists commercially. |
| `input_artifacts` | — | `path@version` references; changing them changes the fingerprint. |
| `dependencies` | — | `task_id`s that must reach `completed` first (edge rows). |
| `allowed_files` | — | File prefixes the specialist may touch. |
| `allowed_tools` | — | Subset of the role's permission set; anything else escalates. |
| `external_actions` | — | Network/publish/spend actions — same permission check. |
| `required_outputs` | — | Expected artifact kinds/refs. |
| `acceptance_criteria` | — | Human/verifier checklist. |
| `verification_method` | yes | How completion is independently checked. |
| `budget_seconds` | yes | Wall-clock bound (handler-enforced timeout). |
| `budget_tokens` | — | Model-token cap (0 = unbounded/local). |
| `budget_usd` | — | Monetary cap (0.0 = zero-spend). |
| `retry_limit` | — | Max attempts before dead-letter. |
| `escalation` | — | Who handles a genuine blocker. |
| `idempotency_key` | — | Dedupe key; same key + different payload is rejected. |

`contract.fingerprint()` hashes the execution-relevant fields; artifacts
are stamped with it so outputs from a superseded contract are
identifiable as stale.

## Example contract (JSON for `monetizeos.py enqueue`)

```json
{
  "task_id": "impl-checkout-metering",
  "process_owner": "billing_engineer",
  "objective": "Add usage metering to the checkout webhook",
  "business_purpose": "Metered billing is required before paid launch",
  "input_artifacts": ["runtime/api.py@HEAD"],
  "dependencies": ["spec-product-contract"],
  "allowed_files": ["runtime/", "tests/"],
  "allowed_tools": ["read", "write", "exec"],
  "external_actions": [],
  "required_outputs": ["metering module", "focused tests"],
  "acceptance_criteria": ["metered events persisted", "tests pass"],
  "verification_method": "pytest tests/test_metering.py -q",
  "budget_seconds": 1800,
  "budget_usd": 0.0,
  "retry_limit": 2,
  "idempotency_key": "metering-impl-v1"
}
```

## CompletionReport fields

`task_id`, `status` (`completed|failed|blocked`), `artifact_refs`,
`files_changed`, `tests_run` (`{name, command, result}`),
`assumptions`, `limitations`, `remaining_risks`, `tokens_used`,
`cost_usd`, `duration_seconds`.

Validation: `completed` requires ≥1 recorded test and all `passed`;
negative consumption is rejected.

## Lifecycle

`pending → ready → running → verifying → completed`, plus `blocked`,
`retry_wait`, `failed`, `cancelled`. The Director moves `verifying →
completed` only after checking the report — a specialist never marks its
own task complete.
