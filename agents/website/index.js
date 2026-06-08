'use strict';
/**
 * agents/website/index.js — ProfitEngine v5.0
 * GitHub commit pipeline with content-hash dedup, sitemap, RSS, required pages.
 */
const axios  = require('axios');
const crypto = require('crypto');
const logger = require('../../core/logger').child('WEBSITE');
const state  = require('../../core/state');
const cfg    = require('../../core/config').get;

function ghHeaders() {
  return { Authorization: `token ${cfg().githubToken}`, Accept: 'application/vnd.github.v3+json', 'Content-Type': 'application/json' };
}
function contentHash(str) { return crypto.createHash('sha256').update(str).digest('hex').slice(0,16); }

async function commitFile(filePath, content, message) {
  if (!cfg().githubToken) { logger.warn('No GITHUB_TOKEN'); return null; }
  const apiBase = `https://api.github.com/repos/${cfg().githubOwner}/${cfg().githubRepo}/contents/${filePath}`;
  // Hash dedup
  const hash = contentHash(content);
  const hashKey = `fhash_${filePath.replace(/\//g,'_')}`;
  if (state.get(hashKey) === hash) { logger.debug(`Skipping unchanged: ${filePath}`); return null; }
  let sha;
  try { const e = await axios.get(apiBase, { headers: ghHeaders(), timeout: 10_000 }); sha = e.data.sha; } catch {}
  try {
    const body = { message, content: Buffer.from(content).toString('base64') };
    if (sha) body.sha = sha;
    const res = await axios.put(apiBase, body, { headers: ghHeaders(), timeout: 15_000 });
    state.set(hashKey, hash);
    logger.info(`Committed: ${filePath}`);
    return res.data;
  } catch (err) { logger.error(`Commit failed: ${filePath} — ${err.message}`); return null; }
}

async function publishPost(post) {
  if (!post?.title || !post?.body) return null;
  const date     = new Date().toISOString().slice(0,10);
  const filename = `${cfg().githubBlogDir}/${date}-${post.slug}.md`;
  let content    = post.body;
  if (!content.startsWith('---')) {
    content = `---\ntitle: "${post.title}"\ndate: "${date}"\ntags: [${(post.keywords||[]).slice(0,5).map(k=>`"${k}"`).join(',')}]\ndescription: "${(post.metaDescription||post.title).slice(0,150)}"\n---\n\n${content}`;
    if (post.schemaMarkup) content += post.schemaMarkup;
  }
  const result = await commitFile(filename, content, `feat(post): ${post.title.slice(0,60)}`);
  if (result) {
    state.push('publishedPosts', { slug: post.slug, title: post.title, date, url: `https://${cfg().siteDomain}/${post.slug}` }, 500);
  }
  return result;
}

async function publishSitemap() {
  const posts = state.get('publishedPosts', []);
  const base  = `https://${cfg().siteDomain}`;
  const urls  = [
    `<url><loc>${base}/</loc><priority>1.0</priority><changefreq>daily</changefreq></url>`,
    `<url><loc>${base}/blog</loc><priority>0.9</priority><changefreq>daily</changefreq></url>`,
    ...['about','contact','privacy'].map(p => `<url><loc>${base}/${p}</loc><priority>0.8</priority><changefreq>monthly</changefreq></url>`),
    ...posts.slice(-200).map(p => `<url><loc>${base}/${p.slug}</loc><lastmod>${p.date}</lastmod><priority>0.7</priority><changefreq>monthly</changefreq></url>`),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>`;
  await commitFile('public/sitemap.xml', xml, 'chore(seo): update sitemap');
}

async function publishRSS() {
  const posts = state.get('publishedPosts', []).slice(-20).reverse();
  const items = posts.map(p => `<item><title><![CDATA[${p.title}]]></title><link>https://${cfg().siteDomain}/${p.slug}</link><pubDate>${new Date(p.date).toUTCString()}</pubDate><guid>https://${cfg().siteDomain}/${p.slug}</guid></item>`).join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>${cfg().businessName}</title><link>https://${cfg().siteDomain}</link><description>Passive income, AI tools, and side hustle strategies</description><lastBuildDate>${new Date().toUTCString()}</lastBuildDate>\n${items}\n</channel></rss>`;
  await commitFile('public/feed.xml', xml, 'chore(rss): update feed');
}

async function publishRequiredPages() {
  const pages = {
    'pages/about.md':   `# About ${cfg().businessName}\n\n${cfg().businessName} helps people build passive income through AI-powered content, affiliate marketing, and print-on-demand.\n\nContact: ${cfg().contactEmail}`,
    'pages/contact.md': `# Contact\n\nEmail: [${cfg().contactEmail}](mailto:${cfg().contactEmail})\n\nWebsite: [${cfg().siteDomain}](https://${cfg().siteDomain})`,
    'pages/privacy.md': `# Privacy Policy\n\nThis site uses cookies for analytics. We participate in the Amazon Associates Program and other affiliate programs. We do not sell your personal data.\n\nContact: ${cfg().contactEmail}`,
    'public/robots.txt': `User-agent: *\nAllow: /\nSitemap: https://${cfg().siteDomain}/sitemap.xml`,
  };
  for (const [path, content] of Object.entries(pages)) {
    await commitFile(path, content, `chore(pages): ${path.split('/').pop()}`);
  }
  logger.info('Required pages published');
}

module.exports = { commitFile, publishPost, publishSitemap, publishRSS, publishRequiredPages };
