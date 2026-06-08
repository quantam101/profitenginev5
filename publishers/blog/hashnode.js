'use strict';
const axios  = require('axios');
const logger = require('../../core/logger').child('HASHNODE');
const cfg    = require('../../core/config').get;
const GQL    = `mutation PublishPost($input: PublishPostInput!) { publishPost(input: $input) { post { id url } } }`;

async function publish(post) {
  if (!cfg().hashnodeApiKey || !cfg().hashnodePublicationId) return false;
  const tags = (post.keywords || []).slice(0,5).map(t => ({ name: t.slice(0,20), slug: t.toLowerCase().replace(/\s+/g,'-').slice(0,20) }));
  for (let i = 1; i <= 3; i++) {
    try {
      const res = await axios.post('https://gql.hashnode.com',
        { query: GQL, variables: { input: { title: post.title, contentMarkdown: post.body, tags, publicationId: cfg().hashnodePublicationId, metaTags: { title: post.title, description: (post.metaDescription||post.title).slice(0,150) }, originalArticleURL: `https://${cfg().siteDomain}/${post.slug||''}` } } },
        { headers: { Authorization: cfg().hashnodeApiKey, 'Content-Type': 'application/json' }, timeout: 20_000 });
      if (res.data?.errors?.length) throw new Error(res.data.errors[0].message);
      const url = res.data?.data?.publishPost?.post?.url;
      logger.info(`Published: ${url}`);
      return url;
    } catch (err) {
      logger.warn(`Attempt ${i}: ${err.message}`);
      if (i < 3) await new Promise(r => setTimeout(r, 4000 * i));
    }
  }
  return false;
}
module.exports = { publish };
