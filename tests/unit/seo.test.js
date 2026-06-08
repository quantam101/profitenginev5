'use strict';
const seo = require('../../agents/seo');

describe('SEO Agent', () => {
  test('injectSchemaMarkup adds LD+JSON', () => {
    const post = { title:'Test', slug:'test', keywords:['kw1'], generatedAt: new Date().toISOString() };
    const r = seo.injectSchemaMarkup(post);
    expect(r.schemaMarkup).toContain('application/ld+json');
    expect(r.schemaMarkup).toContain('BlogPosting');
    expect(r.schemaInjected).toBe(true);
  });
  test('optimizePost returns seoOptimized=true', async () => {
    const orig = require('../../core/llm').generateJSON;
    require('../../core/llm').generateJSON = async () => ({ primary:'test kw', secondary:[], longTail:[], lsi:[], metaDescription:'desc', h1:'H1' });
    const post = { title:'How to make money', body:'## Intro\nGreat content here with lots of words to meet minimum requirements.', keywords:[] };
    const r = await seo.optimizePost(post);
    expect(r.seoOptimized).toBe(true);
    expect(r.schemaInjected).toBe(true);
    expect(Array.isArray(r.keywords)).toBe(true);
    require('../../core/llm').generateJSON = orig;
  });
});
