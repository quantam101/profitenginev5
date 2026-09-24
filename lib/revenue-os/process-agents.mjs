export const PROCESS_AGENTS = Object.freeze([
  { id: 'portfolio_ranker', lane: 'supervisor', process: 'Score demand, buyer intent, reuse, margin, speed, competition, compliance risk, and variable cost.', owner: 'Revenue Supervisor' },
  { id: 'technical_product_architect', lane: 'technical_product', process: 'Select a narrow buyer problem, promise, structure, price hypothesis, and SEO position.', owner: 'Technical Product Agent' },
  { id: 'technical_content_engineer', lane: 'technical_product', process: 'Produce chapters, scripts, code files, README, validation checklist, and verification queue.', owner: 'Technical Product Agent' },
  { id: 'technical_compiler', lane: 'technical_product', process: 'Compile PDF, Typst source, Markdown, code tree, manifest, hashes, and ZIP bundle.', owner: 'Artifact Factory' },
  { id: 'technical_distribution_gate', lane: 'technical_product', process: 'Route the finished bundle only through an authorized storefront adapter or controlled handoff.', owner: 'Distribution Gate' },
  { id: 'stock_concept_researcher', lane: 'stock_asset', process: 'Generate differentiated commercial vector concepts without third-party IP or trademark targeting.', owner: 'Stock Asset Agent' },
  { id: 'stock_vector_renderer', lane: 'stock_asset', process: 'Render deterministic editable SVG vectors locally at commercial resolution.', owner: 'Artifact Factory' },
  { id: 'stock_metadata_optimizer', lane: 'stock_asset', process: 'Generate ordered titles and keyword sets for marketplace search.', owner: 'Stock Asset Agent' },
  { id: 'stock_compliance_gate', lane: 'stock_asset', process: 'Enforce AI disclosure, rights, similarity, format, marketplace, and human-review requirements.', owner: 'Compliance Gate' },
  { id: 'newsletter_source_collector', lane: 'newsletter', process: 'Collect allowlisted RSS/Atom sources, sanitize markup, cap payloads, and deduplicate items.', owner: 'Industry Briefing Agent' },
  { id: 'newsletter_editor', lane: 'newsletter', process: 'Synthesize only supplied evidence into briefing items, implications, actions, SEO metadata, and social snippets.', owner: 'Industry Briefing Agent' },
  { id: 'newsletter_compiler', lane: 'newsletter', process: 'Render escaped HTML, structured JSON, manifest, hashes, and ZIP proof package.', owner: 'Artifact Factory' },
  { id: 'newsletter_distribution_gate', lane: 'newsletter', process: 'Create provider drafts or controlled handoffs only when plan, credentials, and publication controls are valid.', owner: 'Distribution Gate' },
  { id: 'proof_ledger', lane: 'supervisor', process: 'Preserve cycle JSON, artifact hashes, QA results, provider proof, failures, and review queue state.', owner: 'Audit Agent' },
  { id: 'catch_and_correct', lane: 'supervisor', process: 'Compare quality, conversion, acceptance, revenue, refund, cost, and policy rejection signals; propose tested prompt/config changes.', owner: 'Lifelong Catch and Correct' },
]);

function laneResult(cycle, lane) {
  return (cycle?.results || []).find((result) => result.agentId === lane);
}

function laneArtifact(artifacts, lane) {
  return (artifacts?.artifacts || []).find((artifact) => artifact.agentId === lane);
}

export function buildProcessAgentStatus(cycle, artifacts) {
  return PROCESS_AGENTS.map((agent) => {
    if (agent.lane === 'supervisor') {
      return {
        ...agent,
        state: cycle?.ok ? 'completed' : 'attention',
        evidence: cycle?.cycleId || null,
      };
    }
    const result = laneResult(cycle, agent.lane);
    const artifact = laneArtifact(artifacts, agent.lane);
    if (!result) return { ...agent, state: 'not_scheduled', evidence: null };
    if (agent.id.includes('compiler') || agent.id.includes('renderer')) {
      return { ...agent, state: artifact?.ok ? 'completed' : 'attention', evidence: artifact?.sha256 || artifact?.reason || null };
    }
    if (agent.id.includes('distribution_gate') || agent.id.includes('compliance_gate')) {
      return { ...agent, state: result.delivery?.attempted ? (result.delivery?.ok ? 'completed' : 'attention') : 'gated', evidence: result.decision?.mode || result.delivery?.mode || 'review_queue' };
    }
    return { ...agent, state: result.ai?.ok ? 'completed' : 'attention', evidence: result.ai?.provider || null };
  });
}
