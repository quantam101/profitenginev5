import assert from 'node:assert/strict';
import { register } from 'node:module';

register('./next-server-loader.mjs', import.meta.url);

process.env.TOKENFORGE_API_KEY = 'test-tf-key';
delete process.env.GROQ_API_KEY;
delete process.env.GEMINI_API_KEY;

const { POST, GET } = await import('../app/api/tokenforge/route.ts');

function req({ headers = {}, body = null } = {}) {
  return {
    headers: { get: (k) => headers[k.toLowerCase()] ?? null },
    json: async () => {
      if (body === 'INVALID') throw new Error('bad json');
      return body;
    },
  };
}
const authed = (body) => req({ headers: { 'x-tf-key': 'test-tf-key' }, body });
async function call(handler, request) {
  const res = await handler(request);
  return { status: res.status, json: await res.json() };
}

function mockFetch(fn) {
  const orig = globalThis.fetch;
  globalThis.fetch = fn;
  return () => { globalThis.fetch = orig; };
}
const pollinationsOk = async (url, init) => ({
  ok: true, status: 200,
  json: async () => ({ choices: [{ message: { content: 'hello', role: 'assistant' } }], usage: { total_tokens: 5 } }),
});

// auth
{
  const r = await call(POST, req({ body: { prompt: 'hi' } }));
  assert.equal(r.status, 401);
  const bad = await call(POST, req({ headers: { 'x-tf-key': 'wrong' }, body: { prompt: 'hi' } }));
  assert.equal(bad.status, 401);
  const g = await call(GET, req({}));
  assert.equal(g.status, 401);
}
// validation
{
  const r = await call(POST, authed({}));
  assert.equal(r.status, 400);
  const invalid = await call(POST, req({ headers: { 'x-tf-key': 'test-tf-key' }, body: 'INVALID' }));
  assert.equal(invalid.status, 400);
  const paid = await call(POST, authed({ prompt: 'hi', provider: 'anthropic' }));
  assert.equal(paid.status, 400);
  assert.match(paid.json.error, /Free providers only/);
  const huge = await call(POST, authed({ prompt: 'x'.repeat(16001) }));
  assert.equal(huge.status, 413);
}
// auto cascade lands on keyless pollinations when no keys are configured
{
  const restore = mockFetch(pollinationsOk);
  try {
    const r = await call(POST, authed({ prompt: 'hi' }));
    assert.equal(r.status, 200);
    assert.equal(r.json.ok, true);
    assert.equal(r.json.provider, 'pollinations');
    assert.equal(r.json.text, 'hello');
  } finally { restore(); }
}
// max_tokens is clamped and never upstream-controlled
{
  let sentTokens = null;
  const restore = mockFetch(async (url, init) => {
    sentTokens = JSON.parse(init.body).max_tokens;
    return pollinationsOk(url, init);
  });
  try {
    await call(POST, authed({ prompt: 'hi', max_tokens: 999999 }));
    assert.equal(sentTokens, 1024);
    await call(POST, authed({ prompt: 'hi' }));
    assert.equal(sentTokens, 256);
  } finally { restore(); }
}
// model outside the free allowlist is rejected for a pinned provider
{
  const r = await call(POST, authed({ prompt: 'hi', provider: 'pollinations', model: 'gpt-5-pro' }));
  assert.equal(r.status, 502);
  assert.match(r.json.error, /not in free allowlist/);
}
// when every provider errors, the route fails closed with 502
{
  const restore = mockFetch(async () => ({ ok: false, status: 500, json: async () => ({}) }));
  try {
    const r = await call(POST, authed({ prompt: 'hi' }));
    assert.equal(r.status, 502);
    assert.equal(r.json.ok, false);
  } finally { restore(); }
}
// GET reports pollinations as always configured
{
  const g = await call(GET, authed(null));
  assert.equal(g.status, 200);
  assert.equal(g.json.providers.pollinations.keyless, true);
  assert.equal(g.json.cost, 'zero');
}

console.log('tokenforge route tests passed');
