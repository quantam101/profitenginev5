export const commandCenterStatus = {
  agents: {
    title: 'Agents',
    summary: 'Runtime agents are governed by local-first routing, approval gates, and audit logging.',
    items: [
      { label: 'Sovereign core', state: 'pass', detail: 'Deterministic local route is active and covered by runtime tests.' },
      { label: 'Paid model escalation', state: 'locked', detail: 'External execution remains disabled by policy.' },
      { label: 'Local model adapter', state: 'review', detail: 'Route exists, but execution stays unavailable until a verified local adapter is installed.' }
    ]
  },
  approvals: {
    title: 'Approvals',
    summary: 'Risky work is queued before execution and does not run automatically.',
    items: [
      { label: 'Complex work gate', state: 'pass', detail: 'Production deploys, outreach, and other risky tasks require approval.' },
      { label: 'No auto execution', state: 'pass', detail: 'The runtime returns approval_required instead of taking external action.' },
      { label: 'Approval storage', state: 'review', detail: 'File-backed local approval storage is ready for an OCI persistent volume.' }
    ]
  },
  changelog: {
    title: 'Changelog',
    summary: 'Correction history is intentionally small and file-backed until a persistent deployment target is selected.',
    items: [
      { label: 'Dependency security', state: 'pass', detail: 'Next, ESLint, and PostCSS are patched and npm audit is clean.' },
      { label: 'Stale source removal', state: 'pass', detail: 'Old enabled module claims were replaced with disabled stale-source states.' },
      { label: 'Live hosting', state: 'blocked', detail: 'Vercel token or OCI SSH access is still required to publish a durable public endpoint.' }
    ]
  },
  connectors: {
    title: 'Connectors',
    summary: 'Connector posture is no-spend by default and suitable for review before enabling any external account.',
    items: [
      { label: 'Paid adapters', state: 'locked', detail: 'Paid adapters are disabled in runtime policy.' },
      { label: 'Secrets in repo', state: 'pass', detail: 'Security scan found no known secret markers.' },
      { label: 'Provider credentials', state: 'review', detail: 'Credentials must be supplied as environment variables only after key rotation.' }
    ]
  },
  costs: {
    title: 'Costs',
    summary: 'The app is configured to fail closed before any paid or external execution route.',
    items: [
      { label: 'Max spend', state: 'pass', detail: 'Configured max cost is zero dollars.' },
      { label: 'Cloud escalation', state: 'locked', detail: 'External execution is disabled.' },
      { label: 'Usage monitoring', state: 'blocked', detail: 'Uptime and spend monitoring are not live until a durable host is deployed.' }
    ]
  },
  logs: {
    title: 'Logs',
    summary: 'Audit logging is active for runtime decisions and blocked actions.',
    items: [
      { label: 'Audit writer', state: 'pass', detail: 'Runtime emits JSONL audit events.' },
      { label: 'Blocked action events', state: 'pass', detail: 'Approval and cost guard blocks are recorded.' },
      { label: 'Central log sink', state: 'blocked', detail: 'A server log target is still needed for production retention.' }
    ]
  },
  modules: {
    title: 'Modules',
    summary: 'Every stale module entry is disabled until replaced by verified production source.',
    items: [
      { label: 'ProfitEngine', state: 'locked', detail: 'Old shell source is archived; command center build is the active deployable artifact.' },
      { label: 'TradeGate', state: 'locked', detail: 'TradeGate is not exposed through this app until its backend is separately verified.' },
      { label: 'All other modules', state: 'locked', detail: 'No module manifest is enabled while source remains stale.' }
    ]
  },
  security: {
    title: 'Security',
    summary: 'Security posture is clean for source and dependencies, with hosting controls still blocked by infrastructure access.',
    items: [
      { label: 'npm audit', state: 'pass', detail: 'Zero vulnerabilities after dependency patching.' },
      { label: 'Secret scan', state: 'pass', detail: 'Known secret marker scan is clean.' },
      { label: 'Firewall and HTTPS', state: 'blocked', detail: 'Cannot be verified until OCI SSH or a Vercel deployment token is available.' }
    ]
  },
  workflows: {
    title: 'Workflows',
    summary: 'Workflow execution remains local-first with approval requirements for risky work.',
    items: [
      { label: 'Safe local drafts', state: 'pass', detail: 'Deterministic local execution is enabled.' },
      { label: 'Production deploy workflow', state: 'blocked', detail: 'Deploy requires either Vercel auth or OCI SSH access.' },
      { label: 'Rollback', state: 'review', detail: 'Git rollback is available; host-level rollback awaits a durable deployment target.' }
    ]
  }
} as const;
