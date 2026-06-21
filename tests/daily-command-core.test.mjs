import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../lib/daily-command-core.ts', import.meta.url), 'utf8');
const transpiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ES2022,
    target: ts.ScriptTarget.ES2022,
    strict: true,
  },
});

const moduleUrl = `data:text/javascript;base64,${Buffer.from(transpiled.outputText).toString('base64')}`;
const dailyCommand = await import(moduleUrl);

const snapshot = dailyCommand.createDailyCommandSnapshot(
  [
    {
      id: 'WM_01',
      source: 'WORKMARKET',
      category: 'FIELD_SERVICE',
      status: 'READY_TO_ACT',
      revenueStatus: 'BOOKABLE',
      pay: 220,
      durationHours: 2,
      location: { address: 'Gilbert, AZ', zip: '85234', lat: 33.3524, lng: -111.7890 },
      title: 'Gilbert smart-hands dispatch',
    },
    {
      id: 'PAY_01',
      source: 'QUICKBOOKS',
      category: 'PAYMENT_PROTECTION',
      status: 'INVOICED',
      revenueStatus: 'INVOICED',
      invoicedUsd: 650,
      title: 'Open invoice follow-up',
    },
    {
      id: 'FN_03',
      source: 'FIELD_NATION',
      category: 'FIELD_SERVICE',
      status: 'NEW',
      revenueStatus: 'OPPORTUNITY',
      pay: 90,
      durationHours: 1,
      location: { address: 'Queen Creek, AZ', zip: '85142', lat: 33.2484, lng: -111.6342 },
      title: 'Queen Creek low-pay printer call',
    },
    {
      id: 'AW_04',
      source: 'GMAIL',
      category: 'AUTOWORKS',
      status: 'NEW',
      revenueStatus: 'OPPORTUNITY',
      pay: 1200,
      durationHours: 8,
      location: { address: 'Phoenix, AZ', zip: '85001', lat: 33.4484, lng: -112.0740 },
      flags: ['DIESEL'],
      title: 'Diesel fleet repair request',
    },
    {
      id: 'BAD_01',
      source: 'NOT_A_SOURCE',
      category: 'FIELD_SERVICE',
      pay: 500,
    },
  ],
  [],
  { generatedAt: '2026-06-21T12:00:00.000Z' }
);

const byTitle = new Map(snapshot.rankedQueue.map((item) => [item.title, item]));

assert.equal(snapshot.systemHealth, 'DEGRADED');
assert.equal(snapshot.metrics.dailyTargetUsd, 500);
assert.ok(snapshot.metrics.revenueGapUsd >= 0);
assert.equal(byTitle.get('Open invoice follow-up')?.grade, 'A');
assert.ok(byTitle.get('Open invoice follow-up')?.requiresOwnerApproval);
assert.equal(byTitle.get('Queen Creek low-pay printer call')?.grade, 'C');
assert.ok(byTitle.get('Queen Creek low-pay printer call')?.riskFlags.includes('MARGIN_BELOW_LABOR_FLOOR'));
assert.equal(byTitle.get('Diesel fleet repair request')?.grade, 'F');
assert.ok(byTitle.get('Diesel fleet repair request')?.riskFlags.includes('FORBIDDEN_SCOPE_EXCLUSION'));
assert.ok(snapshot.rankedQueue.some((item) => item.riskFlags.includes('QUARANTINED_INPUT')));
assert.match(snapshot.masterDocumentOutput, /Daily Command Engine Export/);
assert.match(snapshot.masterDocumentOutput, /Opportunity value is not counted as confirmed revenue/);

console.log('daily command core test passed');
