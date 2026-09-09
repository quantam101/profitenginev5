export const NEWSLETTER_PILLARS = Object.freeze([
  'Revenue systems: lead capture, attribution, pricing, payment enforcement, and recurring revenue design',
  'Field operations: dispatch, technician workflows, closeout QA, route stacking, and offline resilience',
  'AI build notes: production reliability, security, deployment evidence, failures, fixes, and proof of work',
  'Opportunity intelligence: service-business pain signals, automation offers, implementation economics, and exact next actions',
]);

export function editorialPrompt({ mode = 'ideas', brief = '', audience = 'small-business operators, field-service companies, and technical service providers' } = {}) {
  const common = `Brand: ProfitEngine AI by Already Here LLC.\nAudience: ${audience}.\nEditorial pillars:\n- ${NEWSLETTER_PILLARS.join('\n- ')}\nRules: Be practical, measurable, and evidence-first. Do not invent customer results, revenue, deployments, or market facts. Separate diagnostics such as opens/clicks from realized revenue. Every commercial CTA must be attributable to a specific offer or lead source. Prefer reusable systems over generic AI commentary.`;

  if (mode === 'draft') {
    return `${common}\n\nCreate a newsletter draft from this operator brief:\n${brief}\n\nReturn: title, 3 subject lines, opening, 3-5 sections, one practical checklist, one attributable CTA, and a short evidence-needed section. Do not publish or send anything.`;
  }
  if (mode === 'subject_lines') {
    return `${common}\n\nGenerate 10 concise subject lines and matching preview-text variants for this issue brief:\n${brief}\n\nAvoid clickbait and unsupported claims.`;
  }
  return `${common}\n\nGenerate 12 issue ideas for the next 30 days using this context:\n${brief || 'Prioritize recurring revenue, local-service automation, AI reliability, dispatch workflows, and proof-first implementation.'}\n\nFor each idea provide: working title, audience pain, unique evidence/data needed, monetization path, CTA, and why it is useful now. Do not publish or send anything.`;
}
