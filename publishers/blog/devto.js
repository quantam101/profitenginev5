'use strict';
const axios  = require('axios');
const logger = require('../../core/logger').child('DEVTO');
const cfg    = require('../../core/config').get;

async function publish(post) {
  if (!cfg().devtoApiKey) return false;
  const tags = (post.keywords || []).slice(0,4).map(t => t.toLowerCase().replace(/[^a-z0-9]/g,'').slice(0,20)).filter(Boolean);
  for (let i = 1; i <= 3; i++) {
    try {
      const res = await axios.post('https://dev.to/api/articles',
        { article: { title: post.title, body_markdown: post.body, published: true, tags, canonical_url: `https://${cfg().siteDomain}/${post.slug||''}`, description: post.metaDescription || post.title } },
        { headers: { 'api-key': cfg().devtoApiKey, 'Content-Type': 'application/json' }, timeout: 20_000 });
      logger.info(`Published: ${res.data.url}`);
      return res.data.url;
    } catch (err) {
      logger.warn(`Attempt ${i}: ${err.message}`);
      if (i < 3) await new Promise(r => setTimeout(r, 4000 * i));
    }
  }
  return false;
}
module.exports = { publish };
