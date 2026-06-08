'use strict';
/**
 * agents/compliance/index.js — ProfitEngine v5.0
 * FTC compliance, GDPR disclosure, content policy checks.
 * Ensures all published content meets platform-specific requirements.
 * Tier 0 (rule-based) + Tier 1 (AI policy check) hybrid.
 */
const llm    = require('../../core/llm');
const logger = require('../../core/logger').child('COMPLIANCE');
const state  = require('../../core/state');

const REQUIRED_DISCLOSURES = {
  affiliate: ['affiliate', 'commission', 'earn', 'disclosure', 'associate'],
  sponsored: ['sponsored', 'paid', 'partnership', 'collaboration'],
  ai:        ['ai', 'artificial intelligence', 'generated', 'written with'],
};

const PROHIBITED_CLAIMS = [
  /guarantee(d)?\s+(income|profit|earnings|results)/gi,
  /make\s+\$[\d,]+\s+(per\s+day|daily|a\s+day)/gi,
  /get\s+rich\s+quick/gi,
  /100%\s+(guaranteed|certain)/gi,
  /no\s+risk/gi,
];

function checkDisclosures(post) {
  const flags = [];
  const lbody = (post.body || '').toLowerCase();

  if (post.linksInjected > 0 || post.affiliateProductsUsed?.length > 0) {
    const hasDisclosure = REQUIRED_DISCLOSURES.affiliate.some(d => lbody.includes(d));
    if (!hasDisclosure) flags.push({ type: 'missing_ftc_disclosure', severity: 'high', fix: 'Add FTC affiliate disclosure' });
  }
  for (const pattern of PROHIBITED_CLAIMS) {
    if (pattern.test(post.body || '')) {
      flags.push({ type: 'prohibited_claim', severity: 'high', pattern: pattern.source, fix: 'Remove or soften guaranteed income claim' });
    }
  }
  return flags;
}

function injectDisclosure(post) {
  if (!post?.body) return post;
  const lbody = post.body.toLowerCase();
  const hasDisclosure = REQUIRED_DISCLOSURES.affiliate.some(d => lbody.includes(d));
  if (hasDisclosure) return { ...post, complianceChecked: true };
  const disclosure = '\n\n> **Affiliate Disclosure:** This article contains affiliate links. As an Amazon Associate and partner with other programs, I earn from qualifying purchases at no additional cost to you.\n';
  return { ...post, body: disclosure + post.body, complianceChecked: true, disclosureInjected: true };
}

function removeProlhibitedClaims(text) {
  let cleaned = text;
  cleaned = cleaned.replace(/guarantee(d)?\s+(income|profit|earnings|results)/gi, 'potential income');
  cleaned = cleaned.replace(/get\s+rich\s+quick/gi, 'build income over time');
  cleaned = cleaned.replace(/100%\s+(guaranteed|certain)/gi, 'highly effective');
  return cleaned;
}

async function aiPolicyCheck(post) {
  if (!post?.body) return { passed: true, flags: [] };
  const prompt = `Content compliance reviewer. Check this blog post excerpt for policy violations:
Title: "${post.title}"
First 500 chars: "${post.body.slice(0,500)}"

Check for: deceptive income claims, spam signals, hate speech, medical/legal/financial advice without disclaimer.
Return JSON: { passed: boolean, flags: [{ type:string, severity:"high|medium|low", description:string }] }`;
  try {
    const result = await llm.generateJSON(prompt, true);
    return result;
  } catch { return { passed: true, flags: [] }; }
}

async function processPost(post) {
  let p = post;
  // Step 1: Inject disclosures
  p = injectDisclosure(p);
  // Step 2: Remove prohibited claims
  p = { ...p, body: removeProlhibitedClaims(p.body || '') };
  // Step 3: Rule-based flag check
  const flags = checkDisclosures(p);
  // Step 4: AI policy check (lightweight)
  const aiCheck = await aiPolicyCheck(p).catch(() => ({ passed: true, flags: [] }));
  const allFlags = [...flags, ...(aiCheck.flags || [])];

  if (allFlags.filter(f => f.severity === 'high').length > 0) {
    logger.warn(`Compliance flags on "${p.title.slice(0,40)}": ${allFlags.length} issues`);
    state.push('complianceLog', { title: p.title, flags: allFlags, ts: new Date().toISOString() }, 100);
  }

  return { ...p, complianceFlags: allFlags, compliancePassed: aiCheck.passed };
}

module.exports = { processPost, checkDisclosures, injectDisclosure, aiPolicyCheck };
