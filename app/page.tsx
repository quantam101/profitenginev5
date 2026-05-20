import Link from 'next/link';

const cards = [
  ['Agents', '/command-center/agents', 'Inspect the active registry-driven agent policy.'],
  ['Modules', '/command-center/modules', 'Verify stale module entries are disabled until production source is approved.'],
  ['Workflows', '/command-center/workflows', 'Launch safe local workflows and queue risky work.'],
  ['Approvals', '/command-center/approvals', 'Review pending approvals before any risky action.'],
  ['Costs', '/command-center/costs', 'Confirm strict zero-spend mode and paid adapter lockout.'],
  ['Security', '/command-center/security', 'Review no-spend, secrets, and production gate posture.'],
  ['Logs', '/command-center/logs', 'Read runtime and audit event status.'],
  ['Connectors', '/command-center/connectors', 'Inspect connector state and disable paid paths.'],
  ['Changelog', '/command-center/changelog', 'Lifelong Catch and Correct correction log.']
];

export default function HomePage() {
  return (
    <main className="shell">
      <span className="badge">ProfitEngine / GMAOS</span>
      <h1>ProfitEngine Command Center</h1>
      <p className="muted">Production-gated, zero-spend-first control surface for local agent governance and deployment readiness.</p>
      <div className="grid">
        {cards.map(([title, href, body]) => (
          <Link key={href} href={href} className="card">
            <h2>{title}</h2>
            <p className="muted">{body}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
