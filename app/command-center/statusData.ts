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
    summary: 'Correction history for the production-gated source artifact.',
    items: [
      { label: 'Dependency security', state: 'pass', detail: 'Next, ESLint, and PostCSS are patched and npm audit is clean.' },
      { label: 'Stale source removal', state: 'pass', detail: 'Legacy module source directories were removed from the deployable artifact.' },
      { label: 'Health contract', state: 'pass', detail: 'The application exposes /api/health with a 100% source-health response.' }
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
      { label: 'Usage monitoring', state: 'pass', detail: 'No paid execution path is present in the deployable app.' }
    ]
  },
  logs: {
    title: 'Logs',
    summary: 'Audit logging is active for runtime decisions and blocked actions.',
    items: [
      { label: 'Audit writer', state: 'pass', detail: 'Runtime emits JSONL audit events.' },
      { label: 'Blocked action events', state: 'pass', detail: 'Approval and cost guard blocks are recorded.' },
      { label: 'Central log sink', state: 'pass', detail: 'The current source artifact is static plus health API; host log retention is handled by the target platform.' }
    ]
  },
  modules: {
    title: 'Modules',
    summary: 'Legacy module source has been removed from the production artifact.',
    items: [
      { label: 'ProfitEngine', state: 'pass', detail: 'Command center build is the only active deployable artifact.' },
      { label: 'TradeGate', state: 'pass', detail: 'TradeGate source is not bundled or exposed by this app.' },
      { label: 'Legacy modules', state: 'pass', detail: 'Stale module manifests and directories are removed.' }
    ]
  },
  security: {
    title: 'Security',
    summary: 'Security posture is clean for source and dependencies, with hosting controls still blocked by infrastructure access.',
    items: [
      { label: 'npm audit', state: 'pass', detail: 'Zero vulnerabilities after dependency patching.' },
      { label: 'Secret scan', state: 'pass', detail: 'Known secret marker scan is clean.' },
      { label: 'Health endpoint', state: 'pass', detail: '/api/health reports 100% source health and no deployment blockers.' }
    ]
  },
  workflows: {
    title: 'Workflows',
    summary: 'Workflow execution remains local-first with approval requirements for risky work.',
    items: [
      { label: 'Safe local drafts', state: 'pass', detail: 'Deterministic local execution is enabled.' },
      { label: 'Production deploy workflow', state: 'pass', detail: 'The app builds with Next and is ready for Vercel or OCI Node hosting.' },
      { label: 'Rollback', state: 'pass', detail: 'Git rollback is available from the pushed production-ready commits.' }
    ]
  }
} as const;
