import fs from 'node:fs';
import path from 'node:path';

const seedPaths = [
  path.resolve('data/revenue-os/revenue-plays.seed.json'),
  path.resolve('data/revenue-os/revenue-plays.seed.v1.1.json'),
  path.resolve('data/revenue-os/revenue-plays.seed.v1.2.json'),
  path.resolve('data/revenue-os/revenue-plays.seed.v1.3.json'),
];

const required = [
  'id','source','lane','revenue_play_name','buyer_type',
  'example_target_company_or_market','contact_path','location','pain_solved',
  'estimated_ticket_value','cost_required','profit_potential','time_to_revenue',
  'recurring_potential','stacking_fit','startup_requirements',
  'first_10_target_strategy','risk_flags','recommended_action','status',
  'next_follow_up_date','notes','score_inputs','opportunity_score'
];

const errors = [];
const ids = new Set();
const records = [];

for (const seedPath of seedPaths) {
  const parsed = JSON.parse(fs.readFileSync(seedPath, 'utf8'));
  if (!Array.isArray(parsed.records)) {
    errors.push(`${seedPath}: records must be an array`);
    continue;
  }
  if (parsed.records.length !== parsed.record_count) {
    errors.push(`${seedPath}: declared ${parsed.record_count}, found ${parsed.records.length}`);
  }

  for (const [index, record] of parsed.records.entries()) {
    for (const field of required) {
      if (record[field] === undefined || record[field] === null || record[field] === '') {
        errors.push(`${seedPath}: records[${index}] missing ${field}`);
      }
    }
    if (ids.has(record.id)) errors.push(`duplicate id across datasets: ${record.id}`);
    ids.add(record.id);
    const computed = Object.values(record.score_inputs ?? {}).reduce((sum, value) => sum + Number(value), 0);
    if (computed !== record.opportunity_score) {
      errors.push(`${record.id} opportunity_score ${record.opportunity_score} != computed ${computed}`);
    }
    records.push(record);
  }
}

if (records.length !== 80) errors.push(`combined records length must be 80, got ${records.length}`);

for (let number = 1; number <= 80; number += 1) {
  const expectedId = `RP-${String(number).padStart(3, '0')}`;
  if (!ids.has(expectedId)) errors.push(`missing sequential id ${expectedId}`);
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(`Validated ${records.length} sequential Revenue OS seed records across ${seedPaths.length} datasets.`);
