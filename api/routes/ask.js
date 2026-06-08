'use strict';
/**
 * api/routes/ask.js — ProfitEngine v5.0
 * AI advisor endpoint using Claude API (claude-sonnet-4-20250514).
 * Fallback to local LLM if Claude unavailable.
 */
const express = require('express');
const axios   = require('axios');
const router  = express.Router();
const llm     = require('../../core/llm');
const state   = require('../../core/state');
const cfg     = require('../../core/config').get;
const intel   = require('../../agents/intelligence');

router.post('/', async (req, res) => {
  const { question } = req.body;
  if (!question?.trim()) return res.status(400).json({ error: 'question required' });

  const metrics = {
    generated:   state.get('totalGenerated', 0),
    published:   state.get('totalPublished', 0),
    trends:      state.get('totalTrends', 0),
    lastCycle:   state.get('lastCycle', {}),
    tokens:      llm.todayTokens(),
    circuits:    llm.circuitStatus(),
    health:      state.get('lastHealth', {}),
    intelligence:intel.getReport(),
    revenue:     state.get(`revenue_${new Date().toISOString().slice(0,7)}`, {}),
  };

  // Try Claude API first (injected by claude.ai artifact env)
  try {
    const resp = await axios.post('https://api.anthropic.com/v1/messages', {
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      system: `You are the AI operations advisor for ProfitEngine v5.0 — an autonomous content monetization system for ${cfg().businessName} (${cfg().siteDomain}).
Current metrics: ${JSON.stringify(metrics)}
Be concise, direct, and revenue-focused. Prioritize actionable recommendations.`,
      messages: [{ role: 'user', content: question }],
    }, {
      headers: { 'Content-Type': 'application/json', 'anthropic-version': '2023-06-01' },
      timeout: 30_000,
    });
    const text = resp.data.content?.find(b => b.type === 'text')?.text || '';
    return res.json({ answer: text, source: 'claude' });
  } catch {}

  // Fallback: local LLM
  try {
    const ans = await llm.generate(
      `Operations advisor for ProfitEngine v5.0. Metrics: ${JSON.stringify(metrics)}\n\nQuestion: ${question}`,
      'Be concise and actionable.', 800
    );
    return res.json({ answer: ans, source: 'local' });
  } catch (err) {
    return res.status(503).json({ error: 'AI advisor temporarily unavailable' });
  }
});

module.exports = router;
