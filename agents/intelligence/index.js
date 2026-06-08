'use strict';
/**
 * agents/intelligence/index.js — ProfitEngine v5.0
 * ASI-equivalent meta-controller. Observes all agent outputs,
 * rewrites prompt templates, rebalances platform weights,
 * adjusts niche strategy, enforces quality gates, and
 * generates forward-looking revenue projections.
 * Runs every 6h. Tier 2 only.
 */
const llm    = require('../../core/llm');
const logger = require('../../core/logger').child('INTEL');
const state  = require('../../core/state');
const email  = require('../../core/email');
const cfg    = require('../../core/config').get;

const PROMPT_REGISTRY = {
  trendScoring:    state.get('prompt:trendScoring',    null),
  contentGen:      state.get('prompt:contentGen',      null),
  seoKeywords:     state.get('prompt:seoKeywords',     null),
  socialCaption:   state.get('prompt:socialCaption',   null),
};

async function analyze() {
  logger.info('Intelligence cycle starting...');

  const metrics = {
    cycle:          state.get('cycleCount', 0),
    generated:      state.get('totalGenerated', 0),
    published:      state.get('totalPublished', 0),
    social:         state.get('totalSocial', 0),
    trends:         state.get('totalTrends', 0),
    dlqDepth:       (state.get('dlq', []) || []).length,
    contentPerf:    state.get('contentTypePerf', {}),
    platformPerf:   state.get('platformPerf', {}),
    nichePerf:      state.get('nichePerf', {}),
    revenueEvents:  (state.get('revenueEvents', []) || []).slice(-30),
    publishErrors:  (state.get('publishErrors', []) || []).slice(-10),
    tokens:         llm.todayTokens(),
    circuits:       llm.circuitStatus(),
    lastReport:     state.get('intelligenceReport', {}),
  };

  const prompt = `You are the ASI-equivalent intelligence controller for ProfitEngine v5.0.
Business: ${cfg().businessName} | ${cfg().siteDomain}
Mission: Maximize passive income through autonomous content monetization.

Full system telemetry:
${JSON.stringify(metrics, null, 2)}

Produce a comprehensive intelligence report as JSON:
{
  "healthScore": 0-100,
  "revenueProjection": { "daily": number, "monthly": number, "confidence": "low|medium|high" },
  "criticalIssues": [{ "severity": "critical|high|medium", "issue": string, "action": string }],
  "promptRewrites": [{ "target": string, "rationale": string, "newPromptFragment": string }],
  "nicheStrategy": { "drop": string[], "add": string[], "boost": string[] },
  "platformStrategy": { "increase": string[], "decrease": string[], "rationale": string },
  "contentStrategy": { "bestType": string, "bestLength": number, "keyInsight": string },
  "schedulingOverrides": { "scanIntervalMin": number, "contentPerRun": number },
  "complianceFlags": string[],
  "executiveSummary": string
}`;

  let report;
  try {
    report = await llm.generateJSON(prompt);
  } catch (err) {
    logger.error('Intelligence analysis failed', { error: err.message });
    return null;
  }

  report.generatedAt = new Date().toISOString();
  state.set('intelligenceReport', report);
  state.set('lastIntelligenceCycle', report.generatedAt);

  // Apply prompt rewrites to registry
  if (Array.isArray(report.promptRewrites)) {
    for (const rw of report.promptRewrites) {
      if (rw.target && rw.newPromptFragment) {
        PROMPT_REGISTRY[rw.target] = rw.newPromptFragment;
        state.set(`prompt:${rw.target}`, rw.newPromptFragment);
        logger.info(`Prompt rewrite applied: ${rw.target}`);
      }
    }
  }

  // Apply scheduling overrides within safe bounds
  if (report.schedulingOverrides?.scanIntervalMin) {
    const min = Math.max(10, Math.min(120, report.schedulingOverrides.scanIntervalMin));
    state.set('adaptiveScanInterval', min);
  }
  if (report.schedulingOverrides?.contentPerRun) {
    const cpr = Math.max(1, Math.min(8, report.schedulingOverrides.contentPerRun));
    state.set('adaptiveContentPerRun', cpr);
  }

  // Alert on critical issues
  const criticals = (report.criticalIssues || []).filter(i => i.severity === 'critical');
  if (criticals.length) {
    await email.sendAlert(
      `ProfitEngine Critical: ${criticals.length} issue(s)`,
      criticals.map(i => `[${i.severity.toUpperCase()}] ${i.issue}\nAction: ${i.action}`).join('\n\n')
    );
  }

  logger.info(`Intelligence complete. Health: ${report.healthScore}/100 | Rev projection: $${report.revenueProjection?.monthly}/mo`);
  return report;
}

function getPrompt(key) {
  return PROMPT_REGISTRY[key] || null;
}

function getReport() {
  return state.get('intelligenceReport', null);
}

// Dead letter queue management
function addToDLQ(item, error, agent) {
  const dlq = state.get('dlq', []);
  const existing = dlq.find(d => d.id === item.id);
  if (existing) {
    existing.retries = (existing.retries || 0) + 1;
    existing.lastError = error;
    existing.lastAttempt = new Date().toISOString();
  } else {
    dlq.push({ ...item, agent, retries: 1, lastError: error, addedAt: new Date().toISOString() });
  }
  state.set('dlq', dlq.slice(-200));
}

async function drainDLQ() {
  const dlq = state.get('dlq', []);
  if (!dlq.length) return 0;
  const recoverable = dlq.filter(d => d.retries < 3);
  const dead = dlq.filter(d => d.retries >= 3);
  state.set('dlq', dead);
  state.set('recoveryQueue', recoverable);
  logger.info(`DLQ drained: ${recoverable.length} recoverable, ${dead.length} permanently dead`);
  return recoverable.length;
}

module.exports = { analyze, getPrompt, getReport, addToDLQ, drainDLQ };
