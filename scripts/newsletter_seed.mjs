import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { upsertIssue } from '../lib/newsletter-business/repository.mjs';
import { closeClient } from '../lib/mongodb.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const issuePath = resolve(__dirname, '../data/newsletter/issue-001.json');

async function main() {
  const issue = JSON.parse(await readFile(issuePath, 'utf8'));
  const saved = await upsertIssue(issue);
  console.log(JSON.stringify({
    ok: true,
    slug: saved?.slug,
    status: saved?.status,
    issueId: String(saved?._id || ''),
  }, null, 2));
}

main()
  .catch((error) => {
    console.error('[newsletter:seed] failed:', error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await closeClient().catch(() => {});
  });
