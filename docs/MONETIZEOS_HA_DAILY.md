# MonetizeOS relevance, fenced Director failover and daily verification

Base: \`quantam101/profitenginev5\` main at \`ca85606acc9dd9a9852ee50a7143a863b5cd3a37\`.

This change set is additive to the existing \`runtime/monetizeos\` tree. It
does not merge unrelated PRs or alter production payment/publishing behavior.

## 1. Opportunity qualification

\`runtime/opportunity_relevance.py\` gates admission using supported IT
field-service evidence. Generic phrases such as "it is available", "apply",
and "network marketing" do not count as field-service proof. Pricing,
urgency, distance, and buyer enthusiasm cannot overcome a topic rejection.

\`runtime/opportunity_intelligence.py\` continues the commercial score
after topical qualification. Discarded topics produce no proposal cover
letter. C-grade offers remain in durable data for analysis but are not
sent to the high-signal human-review feed. Human-approved scopes remain
subject to rate, travel, and scope policies.

Run:

\`\`\`bash
python -m pytest -q tests/test_opportunity_relevance.py tests/test_opportunity_intelligence.py
\`\`\`

## 2. Director primary / hot-standby

Two **operating-system processes**, each with its own Store connection and
unique Director identity, must reference the **same local SQLite WAL file**
and project ID.

Terminal or independently supervised process A:

\`\`\`bash
python -m runtime.monetizeos.standby --db data/monetizeos.db --project-id profitengine --mode primary
\`\`\`

Terminal or independently supervised process B:

\`\`\`bash
python -m runtime.monetizeos.standby --db data/monetizeos.db --project-id profitengine --mode standby
\`\`\`

- The active process renews its lease while a specialist child is running.
- The standby retries lease acquisition without stealing a live lease.
- After expiry, the atomic SQLite transaction permits just one Director to
  acquire the next fencing epoch. Writes using the old epoch are rejected.
- A voluntary release permits immediate clean handover.
- Specialist tasks are **at least once**, not exactly once. Callers must
  provide idempotency keys and fence external side effects wherever the
  external system supports it.
- A task already leased by a killed worker may wait for **worker** lease
  expiry before it can be reclaimed, even though the Director has failed
  over.
- This is **same-host failover**. SQLite/WAL over NFS, separate Vercel
  instances, serverless temp storage or cross-region replicas are NOT
  supported by this architecture. Production multi-host HA needs a shared
  transactional leasing implementation.

Acceptance test:

\`\`\`bash
python -m pytest -q tests/test_monetizeos.py tests/test_monetizeos_ha.py
\`\`\`

The two-process test kills the primary without releasing its lease, then
asserts that the standby takes over with a strictly newer epoch and stale
writes fail.

## 3. Daily one-command simulation

Run from repository root:

\`\`\`bash
python scripts/monetizeos_daily.py --simulate --report reports/monetizeos-daily.json
\`\`\`

The sequence is always:

1. **Study:** inspect required source files and run deterministic positive
   and negative topic controls.
2. **Self-Repair simulation:** execute real regression checks, collect
   evidence, and propose bounded remediation if a test fails; **no
   automatic source edits**.
3. **Status report:** write machine-readable \`PASS\`, \`NEEDS_REVIEW\`, or
   \`ERROR\` with stage evidence and nonzero process exit on failure.

\`.github/workflows/monetizeos-daily.yml\` schedules this at **13:15 UTC
(06:15 Phoenix time)** daily and permits manual dispatch. A PR run of
\`.github/workflows/ci.yml\` also executes the entire simulation.

GitHub Actions uses an ephemeral checkout, so this daily simulation
**does not preserve a production SQLite lease or create a permanent
hot-standby**. Run the process pair on a persistent host.

## Operational boundaries / rollback

- Fail closed: no production credentials are embedded; no code patch is
  applied automatically; no irreversible actions.
- Before merge, require the repository CI gates, the independent-process
  takeover test, and evidence that the daily JSON artifact is produced.
- To roll back before merge, close the feature PR; \`main\` is unchanged.
- After merge, revert the feature commit(s); stop the new process pair
  before returning to an earlier Director implementation. Keep a backup
  of the persistent SQLite database before any application rollout.
