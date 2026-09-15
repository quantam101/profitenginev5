import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  buildNewsletterArtifacts,
  buildStockAssetArtifacts,
  buildTechnicalProductArtifacts,
  createTextPdf,
  createZip,
  renderNewsletterHtml,
} from '../lib/revenue-os/artifact-factory.mjs';

test('internal PDF renderer emits a valid PDF header and EOF marker', () => {
  const pdf = createTextPdf('Guide', 'Chapter one\nUseful content.');
  assert.equal(pdf.subarray(0, 5).toString('ascii'), '%PDF-');
  assert.match(pdf.subarray(-64).toString('ascii'), /%%EOF/);
});

test('ZIP renderer emits local and end-of-central-directory signatures', () => {
  const zip = createZip([{ name: 'hello.txt', data: Buffer.from('hello') }]);
  assert.equal(zip.readUInt32LE(0), 0x04034b50);
  assert.equal(zip.readUInt32LE(zip.length - 22), 0x06054b50);
});

test('technical product factory creates real PDF and ZIP deliverables', async () => {
  const root = await mkdtemp(join(tmpdir(), 'profitengine-tech-'));
  const result = await buildTechnicalProductArtifacts({
    id: 'product_test',
    qualityScore: 96,
    profitScore: 88,
    artifactManifest: {
      strategy: { title: 'Secure Network Triage', buyer: 'IT operators', promise: 'Faster incident isolation', suggested_price_usd: 19 },
      build: {
        chapters: [
          { title: 'Triage', typst_body: 'Start with scope, evidence, and a reversible diagnostic plan.' },
          { title: 'Validation', typst_body: 'Validate DNS, routes, interfaces, and logs before remediation.' },
        ],
        code_files: [{ path: 'scripts/diag.ps1', content: 'Get-NetIPConfiguration' }],
        readme: 'Run diagnostics with least privilege.',
      },
    },
  }, root);
  assert.equal(result.ok, true);
  assert.equal((await readFile(result.pdfPath)).subarray(0, 5).toString('ascii'), '%PDF-');
  assert.ok((await stat(result.zipPath)).size > 100);
  assert.match(result.sha256, /^[a-f0-9]{64}$/);
});

test('stock factory creates SVG vectors and disclosure metadata package', async () => {
  const root = await mkdtemp(join(tmpdir(), 'profitengine-stock-'));
  const result = await buildStockAssetArtifacts({
    id: 'stock_test',
    ai: { data: { concepts: [{ title: 'Secure Cloud Network', generation_prompt: 'abstract cloud network', keywords: Array.from({ length: 30 }, (_, i) => `keyword${i + 1}`), category: 'Technology' }] } },
    platformGates: { adobe_stock: { allowed: true }, shutterstock: { allowed: false } },
  }, root);
  assert.equal(result.ok, true);
  assert.equal(result.assetCount, 1);
  const svg = await readFile(join(result.directory, result.files[0]), 'utf8');
  assert.match(svg, /^<\?xml/);
  assert.match(svg, /<svg/);
  const policy = await readFile(join(result.directory, 'submission-policy.json'), 'utf8');
  assert.match(policy, /AI-assisted/);
  assert.match(policy, /shutterstock/);
});

test('newsletter renderer escapes HTML and preserves valid source links', async () => {
  const html = renderNewsletterHtml({ subject: '<Unsafe>', lead: 'Lead', briefing_items: [{ title: 'Item', summary: '<script>x</script>', source_url: 'https://example.com/source' }], implications: [], action_items: [], affiliate_disclosure: 'Disclosure' });
  assert.ok(!html.includes('<Unsafe>'));
  assert.ok(!html.includes('<script>x</script>'));
  assert.match(html, /https:\/\/example\.com\/source/);

  const root = await mkdtemp(join(tmpdir(), 'profitengine-news-'));
  const result = await buildNewsletterArtifacts({ id: 'news_test', ai: { data: { subject: 'Weekly Ops', lead: 'Lead', briefing_items: [], implications: [], action_items: [], affiliate_disclosure: 'Disclosure' } } }, root);
  assert.equal(result.ok, true);
  assert.ok((await stat(result.zipPath)).size > 100);
});
