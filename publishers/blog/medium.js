'use strict';
const axios  = require('axios');
const logger = require('../../core/logger').child('MEDIUM');
const cfg    = require('../../core/config').get;
let _authorId = null;

async function getAuthorId() {
  if (_authorId || cfg().mediumAuthorId) return _authorId || cfg().mediumAuthorId;
  const res = await axios.get('https://api.medium.com/v1/me', { headers: { Authorization: `Bearer ${cfg().mediumApiKey}` }, timeout: 10_000 });
  _authorId = res.data?.data?.id;
  return _authorId;
}

async function publish(post) {
  if (!cfg().mediumApiKey) return false;
  try {
    const authorId = await getAuthorId();
    const tags = (post.keywords || []).slice(0,5).map(t => t.replace(/[^a-zA-Z0-9\s]/g,'').slice(0,25)).filter(Boolean);
    const res = await axios.post(`https://api.medium.com/v1/users/${authorId}/posts`,
      { title: post.title, contentFormat: 'markdown', content: post.body, tags, publishStatus: 'public', canonicalUrl: `https://${cfg().siteDomain}/${post.slug||''}`, notifyFollowers: true },
      { headers: { Authorization: `Bearer ${cfg().mediumApiKey}`, 'Content-Type': 'application/json' }, timeout: 20_000 });
    const url = res.data?.data?.url;
    logger.info(`Published: ${url}`);
    return url;
  } catch (err) { logger.warn(`Failed: ${err.message}`); return false; }
}
module.exports = { publish };
