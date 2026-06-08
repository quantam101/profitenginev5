'use strict';
/**
 * tests/unit/llm.test.js — ProfitEngine v5.0
 * Tests the LLM module's public API surface.
 * Provider-level tests (generate/generateJSON) use the integration test suite
 * where axios is fully mocked. Unit tests here cover pure logic only.
 */
const llm = require('../../core/llm');

describe('LLM — pure exports (no I/O)', () => {
  beforeEach(() => {
    llm.resetBreakers();
  });

  test('circuitStatus returns array', () => {
    expect(Array.isArray(llm.circuitStatus())).toBe(true);
  });

  test('breakerStatus is alias for circuitStatus', () => {
    expect(typeof llm.breakerStatus).toBe('function');
    const s = llm.breakerStatus();
    expect(Array.isArray(s)).toBe(true);
  });

  test('todayTokens returns object with total', () => {
    const t = llm.todayTokens();
    expect(t).toHaveProperty('total');
    expect(typeof t.total).toBe('number');
  });

  test('tokensUsedToday returns non-negative number', () => {
    const t = llm.tokensUsedToday();
    expect(typeof t).toBe('number');
    expect(t).toBeGreaterThanOrEqual(0);
  });

  test('tokenBudgetRemaining returns non-negative number', () => {
    expect(llm.tokenBudgetRemaining()).toBeGreaterThanOrEqual(0);
  });

  test('resetBreakers clears circuit state', () => {
    llm.resetBreakers();
    const status = llm.circuitStatus();
    expect(status.every(s => !s.open)).toBe(true);
  });

  test('generate is exported and is async function', () => {
    expect(typeof llm.generate).toBe('function');
    expect(llm.generate.constructor.name).toBe('AsyncFunction');
  });

  test('generateJSON is exported and is async function', () => {
    expect(typeof llm.generateJSON).toBe('function');
    expect(llm.generateJSON.constructor.name).toBe('AsyncFunction');
  });

  test('callFast is exported and is async function', () => {
    expect(typeof llm.callFast).toBe('function');
    expect(llm.callFast.constructor.name).toBe('AsyncFunction');
  });

  test('callFull is exported and is async function', () => {
    expect(typeof llm.callFull).toBe('function');
    expect(llm.callFull.constructor.name).toBe('AsyncFunction');
  });

  test('tokenBudgetRemaining respects DAILY_TOKEN_LIMIT env var', () => {
    const original = process.env.DAILY_TOKEN_LIMIT;
    process.env.DAILY_TOKEN_LIMIT = '1000';
    llm.resetBreakers();
    const remaining = llm.tokenBudgetRemaining();
    expect(remaining).toBeLessThanOrEqual(1000);
    expect(remaining).toBeGreaterThanOrEqual(0);
    if (original) process.env.DAILY_TOKEN_LIMIT = original;
    else delete process.env.DAILY_TOKEN_LIMIT;
  });
});
