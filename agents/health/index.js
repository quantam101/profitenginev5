'use strict';
/**
 * agents/health/index.js — ProfitEngine v5.0
 * Tier 0 only — zero tokens. System vitals: memory, CPU, LLM ping,
 * GitHub ping, cache stats, state size. Alert with cooldown.
 */
const os     = require('os');
const axios  = require('axios');
const logger = require('../../core/logger').child('HEALTH');
const state  = require('../../core/state');
const email  = require('../../core/email');
const cache  = require('../../core/cache');
const llm    = require('../../core/llm');
const cfg    = require('../../core/config').get;

const ALERT_COOLDOWN = 30 * 60_000;

async function pingLLM() {
  try { const r = await llm.callFast('Reply OK', null, 5); return { ok: !!r }; }
  catch { return { ok: false }; }
}

async function pingGitHub() {
  if (!cfg().githubToken) return { ok: false, reason: 'no token' };
  try {
    await axios.get(`https://api.github.com/repos/${cfg().githubOwner}/${cfg().githubRepo}`,
      { headers: { Authorization: `token ${cfg().githubToken}` }, timeout: 8000 });
    return { ok: true };
  } catch (err) { return { ok: false, reason: err.message }; }
}

async function runCheck() {
  const mem  = os.totalmem(), free = os.freemem();
  const load = os.loadavg();
  const cores = os.cpus().length;
  const [llmStatus, ghStatus] = await Promise.allSettled([pingLLM(), pingGitHub()]);

  const status = {
    ts:       new Date().toISOString(),
    uptime:   Math.round(process.uptime() / 60),
    memory:   { totalMB: Math.round(mem/1024/1024), freeMB: Math.round(free/1024/1024), usedPct: Math.round((mem-free)/mem*100) },
    cpu:      { cores, load1: load[0].toFixed(2), load5: load[1].toFixed(2) },
    llm:      llmStatus.status === 'fulfilled' ? llmStatus.value : { ok: false },
    github:   ghStatus.status  === 'fulfilled' ? ghStatus.value  : { ok: false },
    tokens:   llm.todayTokens(),
    circuits: llm.circuitStatus(),
    cache:    cache.stats(),
    dlq:      (state.get('dlq', []) || []).length,
    cycles:   state.get('cycleCount', 0),
  };

  state.set('lastHealth', status);
  logger.info('Health check', { memPct: status.memory.usedPct, cpu: status.cpu.load1, llm: status.llm.ok, github: status.github.ok });

  // Alert logic with cooldown
  const alerts = state.get('healthAlerts', {});
  const now    = Date.now();
  const issues = [];
  if (status.memory.usedPct > 90)                       issues.push(`Memory critical: ${status.memory.usedPct}%`);
  if (!status.llm.ok)                                   issues.push('All LLM providers unreachable');
  if (!status.github.ok && cfg().githubToken)            issues.push(`GitHub unreachable: ${status.github.reason}`);
  if (parseFloat(status.cpu.load1) > cores * 2.5)       issues.push(`CPU overloaded: ${status.cpu.load1}`);
  if (status.dlq > 20)                                  issues.push(`Dead letter queue depth: ${status.dlq}`);

  for (const issue of issues) {
    const k = issue.slice(0,40).replace(/\s+/g,'_');
    if (!alerts[k] || now - alerts[k] > ALERT_COOLDOWN) {
      await email.sendAlert('Health Alert', `${issue}\n\nFull status:\n${JSON.stringify(status, null, 2)}`);
      alerts[k] = now;
    }
  }
  state.set('healthAlerts', alerts);
  return status;
}

module.exports = { runCheck, pingLLM, pingGitHub };
