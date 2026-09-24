import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { basename, dirname, join, relative, resolve } from 'node:path';

function slugify(value, fallback = 'asset') {
  const slug = String(value || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 90);
  return slug || fallback;
}

function safeRelativePath(value, fallback = 'file.txt') {
  const clean = String(value || fallback)
    .replace(/\\/g, '/')
    .split('/')
    .filter((part) => part && part !== '.' && part !== '..')
    .map((part) => part.replace(/[^a-zA-Z0-9._-]+/g, '_').slice(0, 100))
    .filter(Boolean)
    .join('/');
  return clean || fallback;
}

function csvCell(value) {
  const text = String(value ?? '');
  return `"${text.replace(/"/g, '""')}"`;
}

function hashBytes(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

function seededRandom(seedText) {
  const seed = createHash('sha256').update(String(seedText)).digest();
  let state = seed.readUInt32LE(0) || 1;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 0xffffffff;
  };
}

function escapeXml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function stripFormatting(value) {
  return String(value ?? '')
    .replace(/```[a-zA-Z0-9_-]*\n?/g, '')
    .replace(/```/g, '')
    .replace(/^\s*=+\s*/gm, '')
    .replace(/#pagebreak\(\)/g, '\n')
    .replace(/\*\*/g, '')
    .replace(/__+/g, '')
    .replace(/`/g, '')
    .replace(/\r/g, '')
    .trim();
}

function wrapText(text, width = 88) {
  const output = [];
  for (const paragraph of String(text || '').split('\n')) {
    if (!paragraph.trim()) {
      output.push('');
      continue;
    }
    const indent = paragraph.match(/^\s*/)?.[0] || '';
    const words = paragraph.trim().split(/\s+/);
    let line = indent;
    for (const word of words) {
      const next = line.trim() ? `${line} ${word}` : `${indent}${word}`;
      if (next.length > width && line.trim()) {
        output.push(line);
        line = `${indent}${word}`;
      } else {
        line = next;
      }
    }
    if (line.length) output.push(line);
  }
  return output;
}

function pdfEscape(value) {
  return String(value)
    .replace(/[^\x20-\x7E]/g, '?')
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)');
}

function createTextPdf(title, body) {
  const lines = [String(title || 'Technical Guide'), '', ...wrapText(stripFormatting(body), 92)];
  const pageLineCount = 56;
  const pages = [];
  for (let i = 0; i < lines.length; i += pageLineCount) pages.push(lines.slice(i, i + pageLineCount));
  if (!pages.length) pages.push(['']);

  const objects = [];
  const add = (content) => {
    objects.push(content);
    return objects.length;
  };

  const catalogId = add('');
  const pagesId = add('');
  const fontId = add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  const pageIds = [];

  for (const pageLines of pages) {
    const commands = ['BT', '/F1 10 Tf', '48 744 Td', '12 TL'];
    pageLines.forEach((line, index) => {
      if (index > 0) commands.push('T*');
      commands.push(`(${pdfEscape(line)}) Tj`);
    });
    commands.push('ET');
    const stream = commands.join('\n');
    const contentId = add(`<< /Length ${Buffer.byteLength(stream, 'ascii')} >>\nstream\n${stream}\nendstream`);
    const pageId = add(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`);
    pageIds.push(pageId);
  }

  objects[catalogId - 1] = `<< /Type /Catalog /Pages ${pagesId} 0 R >>`;
  objects[pagesId - 1] = `<< /Type /Pages /Count ${pageIds.length} /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}] >>`;

  const header = Buffer.from('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n', 'binary');
  const chunks = [header];
  const offsets = [0];
  let cursor = header.length;
  objects.forEach((object, index) => {
    offsets.push(cursor);
    const chunk = Buffer.from(`${index + 1} 0 obj\n${object}\nendobj\n`, 'binary');
    chunks.push(chunk);
    cursor += chunk.length;
  });
  const xrefOffset = cursor;
  const xref = [
    `xref\n0 ${objects.length + 1}\n`,
    '0000000000 65535 f \n',
    ...offsets.slice(1).map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`),
    `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`,
  ].join('');
  chunks.push(Buffer.from(xref, 'ascii'));
  return Buffer.concat(chunks);
}

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function dosTimestamp(date = new Date()) {
  const year = Math.max(1980, date.getFullYear());
  const time = ((date.getHours() & 0x1f) << 11) | ((date.getMinutes() & 0x3f) << 5) | ((Math.floor(date.getSeconds() / 2)) & 0x1f);
  const day = date.getDate() & 0x1f;
  const month = (date.getMonth() + 1) & 0x0f;
  const dosDate = (((year - 1980) & 0x7f) << 9) | (month << 5) | day;
  return { time, date: dosDate };
}

function createZip(entries) {
  const localParts = [];
  const centralParts = [];
  let offset = 0;
  const stamp = dosTimestamp();

  for (const entry of entries) {
    const name = Buffer.from(entry.name.replace(/\\/g, '/'), 'utf8');
    const data = Buffer.isBuffer(entry.data) ? entry.data : Buffer.from(entry.data);
    const crc = crc32(data);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0, 6);
    local.writeUInt16LE(0, 8);
    local.writeUInt16LE(stamp.time, 10);
    local.writeUInt16LE(stamp.date, 12);
    local.writeUInt32LE(crc, 14);
    local.writeUInt32LE(data.length, 18);
    local.writeUInt32LE(data.length, 22);
    local.writeUInt16LE(name.length, 26);
    local.writeUInt16LE(0, 28);
    localParts.push(local, name, data);

    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(20, 4);
    central.writeUInt16LE(20, 6);
    central.writeUInt16LE(0, 8);
    central.writeUInt16LE(0, 10);
    central.writeUInt16LE(stamp.time, 12);
    central.writeUInt16LE(stamp.date, 14);
    central.writeUInt32LE(crc, 16);
    central.writeUInt32LE(data.length, 20);
    central.writeUInt32LE(data.length, 24);
    central.writeUInt16LE(name.length, 28);
    central.writeUInt16LE(0, 30);
    central.writeUInt16LE(0, 32);
    central.writeUInt16LE(0, 34);
    central.writeUInt16LE(0, 36);
    central.writeUInt32LE(0, 38);
    central.writeUInt32LE(offset, 42);
    centralParts.push(central, name);
    offset += local.length + name.length + data.length;
  }

  const centralDirectory = Buffer.concat(centralParts);
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0);
  eocd.writeUInt16LE(0, 4);
  eocd.writeUInt16LE(0, 6);
  eocd.writeUInt16LE(entries.length, 8);
  eocd.writeUInt16LE(entries.length, 10);
  eocd.writeUInt32LE(centralDirectory.length, 12);
  eocd.writeUInt32LE(offset, 16);
  eocd.writeUInt16LE(0, 20);
  return Buffer.concat([...localParts, centralDirectory, eocd]);
}

async function listFiles(root, current = root) {
  const entries = [];
  for (const name of await readdir(current)) {
    const full = join(current, name);
    const info = await stat(full);
    if (info.isDirectory()) entries.push(...await listFiles(root, full));
    else entries.push({ full, name: relative(root, full).replace(/\\/g, '/') });
  }
  return entries;
}

async function buildManifest(root, exclude = new Set()) {
  const files = [];
  for (const file of await listFiles(root)) {
    if (exclude.has(file.name)) continue;
    const data = await readFile(file.full);
    files.push({ path: file.name, bytes: data.length, sha256: hashBytes(data) });
  }
  return files.sort((a, b) => a.path.localeCompare(b.path));
}

function normalizeChapters(build) {
  const chapters = Array.isArray(build?.chapters) ? build.chapters : [];
  return chapters
    .filter((chapter) => chapter && typeof chapter === 'object')
    .map((chapter, index) => ({
      title: String(chapter.title || `Chapter ${index + 1}`).slice(0, 180),
      body: String(chapter.typst_body || chapter.body || chapter.content || '').trim(),
    }))
    .filter((chapter) => chapter.body);
}

function technicalMarkdown(strategy, build) {
  const title = String(strategy?.title || 'Technical Implementation Guide');
  const buyer = String(strategy?.buyer || 'Technical operators');
  const promise = String(strategy?.promise || 'A practical, reusable implementation reference.');
  const chapters = normalizeChapters(build);
  const chapterText = chapters.map((chapter) => `## ${chapter.title}\n\n${stripFormatting(chapter.body)}`).join('\n\n');
  return `# ${title}\n\n**Audience:** ${buyer}\n\n${promise}\n\n${chapterText}\n`;
}

function technicalTypst(strategy, build) {
  const title = String(strategy?.title || 'Technical Implementation Guide').replace(/[\[\]{}#]/g, '');
  const chapters = normalizeChapters(build);
  const body = chapters.map((chapter) => `= ${chapter.title.replace(/[\[\]{}#]/g, '')}\n\n${chapter.body}\n\n#pagebreak()`).join('\n\n');
  return `#set page(paper: "us-letter", margin: (x: 0.8in, y: 0.8in))\n#set text(font: "Liberation Sans", size: 10.5pt)\n#set heading(numbering: "1.1")\n\n#align(center)[#text(24pt, weight: "bold")[${title}]]\n\n#pagebreak()\n#outline(indent: auto)\n#pagebreak()\n\n${body}\n`;
}

export async function buildTechnicalProductArtifacts(result, rootDir) {
  const strategy = result?.artifactManifest?.strategy;
  const build = result?.artifactManifest?.build;
  if (!strategy || !build) return { ok: false, reason: 'structured strategy/build data unavailable' };
  const chapters = normalizeChapters(build);
  if (!chapters.length) return { ok: false, reason: 'no complete chapters available' };

  const slug = slugify(strategy.title, result?.id || 'technical-product');
  const dir = resolve(rootDir, 'technical-products', slug);
  await mkdir(dir, { recursive: true });
  const markdown = technicalMarkdown(strategy, build);
  const pdf = createTextPdf(strategy.title, markdown);
  await writeFile(join(dir, `${slug}.md`), markdown, 'utf8');
  await writeFile(join(dir, `${slug}.typ`), technicalTypst(strategy, build), 'utf8');
  await writeFile(join(dir, `${slug}.pdf`), pdf);
  await writeFile(join(dir, 'product.json'), `${JSON.stringify({ strategy, qualityScore: result.qualityScore, profitScore: result.profitScore }, null, 2)}\n`, 'utf8');
  await writeFile(join(dir, 'README.md'), `${String(build.readme || 'Technical product bundle generated by ProfitEngine.') }\n`, 'utf8');

  const codeFiles = Array.isArray(build.code_files) ? build.code_files : [];
  for (let index = 0; index < codeFiles.length; index += 1) {
    const file = codeFiles[index];
    if (!file || typeof file !== 'object' || !String(file.content || '').trim()) continue;
    const path = safeRelativePath(file.path, `snippet-${index + 1}.txt`);
    const destination = join(dir, 'code', path);
    await mkdir(dirname(destination), { recursive: true });
    await writeFile(destination, String(file.content), 'utf8');
  }

  const manifestFiles = await buildManifest(dir, new Set(['manifest.json', `${slug}.zip`]));
  const manifest = {
    kind: 'technical_product',
    generatedAt: new Date().toISOString(),
    title: strategy.title,
    qualityScore: result.qualityScore,
    profitScore: result.profitScore,
    files: manifestFiles,
  };
  await writeFile(join(dir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  const zipFiles = await listFiles(dir);
  const zipEntries = [];
  for (const file of zipFiles) {
    if (file.name.endsWith('.zip')) continue;
    zipEntries.push({ name: file.name, data: await readFile(file.full) });
  }
  const zipPath = join(dir, `${slug}.zip`);
  await writeFile(zipPath, createZip(zipEntries));
  return {
    ok: true,
    kind: 'technical_product',
    title: strategy.title,
    directory: dir,
    pdfPath: join(dir, `${slug}.pdf`),
    zipPath,
    sha256: hashBytes(await readFile(zipPath)),
    fileCount: zipEntries.length,
  };
}

function conceptKeywords(concept) {
  const raw = Array.isArray(concept?.keywords)
    ? concept.keywords
    : String(concept?.keywords || '').split(',');
  return raw.map((item) => String(item).trim()).filter(Boolean).slice(0, 30);
}

function renderVectorConcept(concept, index) {
  const title = String(concept?.title || `Technology Vector ${index + 1}`);
  const rand = seededRandom(`${title}|${concept?.generation_prompt || ''}|${index}`);
  const palettes = [
    ['#07111f', '#36d1dc', '#5b86e5', '#e2f3ff'],
    ['#101322', '#7c3aed', '#22d3ee', '#f8fafc'],
    ['#071a18', '#14b8a6', '#84cc16', '#ecfeff'],
    ['#18120b', '#f59e0b', '#ef4444', '#fff7ed'],
  ];
  const colors = palettes[Math.floor(rand() * palettes.length) % palettes.length];
  const nodes = [];
  const links = [];
  const points = Array.from({ length: 28 }, (_, i) => ({
    x: Math.round(220 + rand() * 3656),
    y: Math.round(220 + rand() * 3656),
    r: Math.round(12 + rand() * 34),
    i,
  }));
  for (let i = 0; i < points.length; i += 1) {
    const point = points[i];
    nodes.push(`<circle cx="${point.x}" cy="${point.y}" r="${point.r}" fill="${colors[3]}" fill-opacity="${(0.45 + rand() * 0.45).toFixed(2)}"/>`);
    const next = points[(i + 3 + Math.floor(rand() * 8)) % points.length];
    links.push(`<path d="M ${point.x} ${point.y} Q ${Math.round((point.x + next.x) / 2 + (rand() - 0.5) * 520)} ${Math.round((point.y + next.y) / 2 + (rand() - 0.5) * 520)} ${next.x} ${next.y}" fill="none" stroke="${colors[2]}" stroke-opacity="0.36" stroke-width="${Math.round(5 + rand() * 13)}"/>`);
  }
  const polygons = Array.from({ length: 9 }, () => {
    const cx = 200 + rand() * 3696;
    const cy = 200 + rand() * 3696;
    const size = 140 + rand() * 460;
    const pts = Array.from({ length: 6 }, (_, p) => {
      const a = (Math.PI * 2 * p) / 6;
      return `${Math.round(cx + Math.cos(a) * size)},${Math.round(cy + Math.sin(a) * size)}`;
    }).join(' ');
    return `<polygon points="${pts}" fill="${colors[1]}" fill-opacity="${(0.025 + rand() * 0.07).toFixed(3)}" stroke="${colors[1]}" stroke-opacity="0.16" stroke-width="8"/>`;
  });
  return `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="4096" height="4096" viewBox="0 0 4096 4096" role="img" aria-label="${escapeXml(title)}">\n<defs><radialGradient id="bg" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="${colors[0]}"/><stop offset="1" stop-color="#020617"/></radialGradient><filter id="glow"><feGaussianBlur stdDeviation="16" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>\n<rect width="4096" height="4096" fill="url(#bg)"/>\n${polygons.join('\n')}\n<g>${links.join('\n')}</g>\n<g filter="url(#glow)">${nodes.join('\n')}</g>\n</svg>\n`;
}

export async function buildStockAssetArtifacts(result, rootDir) {
  const payload = result?.ai?.data;
  const concepts = Array.isArray(payload?.concepts) ? payload.concepts.filter(Boolean).slice(0, 12) : [];
  if (!concepts.length) return { ok: false, reason: 'structured stock concepts unavailable' };
  const batchId = slugify(result?.id || `stock-${Date.now()}`, 'stock-batch');
  const dir = resolve(rootDir, 'stock-assets', batchId);
  await mkdir(dir, { recursive: true });
  const csvRows = [['Filename', 'Title', 'Keywords', 'Category', 'AI_Disclosure', 'Review_Status']];
  const files = [];

  for (let index = 0; index < concepts.length; index += 1) {
    const concept = concepts[index];
    const title = String(concept.title || `Technology Vector ${index + 1}`).slice(0, 70);
    const name = `${String(index + 1).padStart(2, '0')}-${slugify(title, `vector-${index + 1}`)}.svg`;
    const svg = renderVectorConcept(concept, index);
    await writeFile(join(dir, name), svg, 'utf8');
    const keywords = conceptKeywords(concept);
    csvRows.push([name, title, keywords.join(', '), String(concept.category || 'Technology'), 'Generative AI / AI-assisted concept', 'Human contributor review required']);
    files.push(name);
  }
  const csv = csvRows.map((row) => row.map(csvCell).join(',')).join('\n') + '\n';
  await writeFile(join(dir, 'stock_upload.csv'), csv, 'utf8');
  await writeFile(join(dir, 'submission-policy.json'), `${JSON.stringify({
    adobe_stock: result.platformGates?.adobe_stock,
    shutterstock: result.platformGates?.shutterstock,
    disclosure: 'All generated concepts are marked AI-assisted and require final rights/quality review before marketplace submission.',
  }, null, 2)}\n`, 'utf8');

  const manifestFiles = await buildManifest(dir, new Set(['manifest.json', `${batchId}.zip`]));
  await writeFile(join(dir, 'manifest.json'), `${JSON.stringify({ kind: 'stock_asset_batch', generatedAt: new Date().toISOString(), files: manifestFiles }, null, 2)}\n`, 'utf8');
  const zipFiles = await listFiles(dir);
  const zipEntries = [];
  for (const file of zipFiles) {
    if (file.name.endsWith('.zip')) continue;
    zipEntries.push({ name: file.name, data: await readFile(file.full) });
  }
  const zipPath = join(dir, `${batchId}.zip`);
  await writeFile(zipPath, createZip(zipEntries));
  return { ok: true, kind: 'stock_asset_batch', directory: dir, zipPath, sha256: hashBytes(await readFile(zipPath)), assetCount: files.length, files };
}

function renderNewsletterHtml(data = {}) {
  const esc = (value) => escapeXml(String(value ?? ''));
  const items = Array.isArray(data.briefing_items) ? data.briefing_items : [];
  const implications = Array.isArray(data.implications) ? data.implications : [];
  const actions = Array.isArray(data.action_items) ? data.action_items : [];
  const itemHtml = items.map((item) => {
    if (typeof item === 'string') return `<li>${esc(item)}</li>`;
    const title = esc(item?.title || item?.headline || 'Briefing item');
    const summary = esc(item?.summary || item?.text || item?.implication || '');
    const url = String(item?.source_url || item?.url || '').trim();
    const source = /^https?:\/\//i.test(url) ? `<p><a href="${esc(url)}">Source</a></p>` : '';
    return `<li><strong>${title}</strong><p>${summary}</p>${source}</li>`;
  }).join('\n');
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(data.subject || data.seo_title || 'Industry Briefing')}</title></head><body><main style="max-width:720px;margin:auto;font-family:Arial,sans-serif;line-height:1.55;padding:24px"><h1>${esc(data.subject || 'Industry Briefing')}</h1><p>${esc(data.lead || '')}</p><h2>Briefing</h2><ul>${itemHtml}</ul><h2>Implications</h2><ul>${implications.map((x) => `<li>${esc(typeof x === 'string' ? x : JSON.stringify(x))}</li>`).join('')}</ul><h2>Actions</h2><ul>${actions.map((x) => `<li>${esc(typeof x === 'string' ? x : JSON.stringify(x))}</li>`).join('')}</ul><hr><p><small>${esc(data.affiliate_disclosure || 'Disclosure: any compensated recommendation will be identified as such.')}</small></p></main></body></html>`;
}

export async function buildNewsletterArtifacts(result, rootDir) {
  const data = result?.ai?.data;
  if (!data?.subject) return { ok: false, reason: 'structured newsletter draft unavailable' };
  const slug = slugify(data.subject, result?.id || 'newsletter');
  const dir = resolve(rootDir, 'newsletters', slug);
  await mkdir(dir, { recursive: true });
  const html = renderNewsletterHtml(data);
  await writeFile(join(dir, `${slug}.html`), html, 'utf8');
  await writeFile(join(dir, `${slug}.json`), `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  const manifestFiles = await buildManifest(dir, new Set(['manifest.json', `${slug}.zip`]));
  await writeFile(join(dir, 'manifest.json'), `${JSON.stringify({ kind: 'newsletter_draft', generatedAt: new Date().toISOString(), files: manifestFiles }, null, 2)}\n`, 'utf8');
  const zipEntries = [];
  for (const file of await listFiles(dir)) {
    if (file.name.endsWith('.zip')) continue;
    zipEntries.push({ name: file.name, data: await readFile(file.full) });
  }
  const zipPath = join(dir, `${slug}.zip`);
  await writeFile(zipPath, createZip(zipEntries));
  return { ok: true, kind: 'newsletter_draft', directory: dir, htmlPath: join(dir, `${slug}.html`), zipPath, sha256: hashBytes(await readFile(zipPath)) };
}

export async function materializeCycleArtifacts(cycle, rootDir) {
  await mkdir(rootDir, { recursive: true });
  const artifacts = [];
  for (const result of cycle?.results || []) {
    if (result.agentId === 'technical_product') artifacts.push({ agentId: result.agentId, ...await buildTechnicalProductArtifacts(result, rootDir) });
    if (result.agentId === 'stock_asset') artifacts.push({ agentId: result.agentId, ...await buildStockAssetArtifacts(result, rootDir) });
    if (result.agentId === 'newsletter') artifacts.push({ agentId: result.agentId, ...await buildNewsletterArtifacts(result, rootDir) });
  }
  const index = {
    cycleId: cycle?.cycleId || null,
    generatedAt: new Date().toISOString(),
    artifacts,
  };
  await writeFile(join(rootDir, 'artifact-index.json'), `${JSON.stringify(index, null, 2)}\n`, 'utf8');
  return index;
}

export { createTextPdf, createZip, renderNewsletterHtml, renderVectorConcept, slugify };
