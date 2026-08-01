import fs from 'node:fs';
import path from 'node:path';

const seedPath = path.resolve('data/revenue-os/revenue-plays.seed.json');
const parsed = JSON.parse(fs.readFileSync(seedPath, 'utf8'));

const required = [
  'id','source','lane','revenue_play_name','buyer_type',
  'example_target_company_or_market','contact_path','location','pain_solved',
  'estimated_ticket_value','cost_required','profit_potential','time_to_revenue',
  'recurring_potential','stacking_fit','startup_requirements',
  'first_10_target_strategy','risk_flags','recommended_action','status',
  'next_follow_up_date','notes','score_inputs','opportunity_score'
];

const errors = [];
if (parsed.record_count !== 65) errors.push(`record_count must be 65, got ${parsed.record_count}`);
if (!Array.isArray(parsed.records)) errors.push('records must be an array');

const ids = new Set();
for (const [index, record] of parsed.records.entries()) {
  for (const field of required) {
    if (record[field] === undefined || record[field] === null || record[field] === '') {
      errors.push(`records[${index}] missing ${field}`);
    }
  }
  if (ids.has(record.id)) errors.push(`duplicate id ${record.id}`);
  ids.add(record.id);
  const computed = Object.values(record.score_inputs ?? {}).reduce((sum, value) => sum + Number(value), 0);
  if (computed !== record.opportunity_score) {
    errors.push(`${record.id} opportunity_score ${record.opportunity_score} != computed ${computed}`);
  }
}

if (parsed.records?.length !== 65) errors.push(`records length must be 65, got ${parsed.records?.length}`);

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(`Validated ${parsed.records.length} Revenue OS seed records.`);
