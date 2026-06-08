'use strict';
/**
 * agents/social/index.js — ProfitEngine v5.0
 * Multi-platform social distribution: Mastodon, Reddit, Pinterest.
 * Per-platform rate limiting, engagement tracking, UCB1 ordering.
 * Twitter: graceful no-op (requires paid tier).
 */
const axios   = require('axios');
const logger  = require('../../core/logger').child('SOCIAL');
const state   = require('../../core/state');
const cfg     = require('../../core/config').get;
const content = require('../content');

const RATE_LIMITS = { mastodon: 60_000, reddit: 10 * 60_000, pinterest: 5 * 60_000 };
const NICHE_SUBREDDITS = {
  'passive income':'passive_income','ai tools':'artificial','side hustle':'sidehustle',
  'print on demand':'printondemand','affiliate marketing':'affiliatemarketing','blogging':'blogging',
};

function rateCheck(platform) {
  const key  = `social_last_${platform}`;
  const last = state.get(key, 0);
  if (Date.now() - last < RATE_LIMITS[platform]) return false;
  return true;
}
function rateRecord(platform) { state.set(`social_last_${platform}`, Date.now()); }
function recordEngagement(platform, score = 1) {
  const perf = state.get('platformPerf', {});
  perf[platform] = (perf[platform] || 0) + score;
  state.set('platformPerf', perf);
}

async function postMastodon(post) {
  if (!cfg().mastodonAccessToken) return false;
  if (!rateCheck('mastodon')) { logger.debug('Mastodon rate limited'); return false; }
  try {
    const caption = await content.generateSocialCaption(post, 'mastodon');
    const res = await axios.post(
      `https://${cfg().mastodonInstance}/api/v1/statuses`,
      { status: caption.slice(0, 490), visibility: 'public' },
      { headers: { Authorization: `Bearer ${cfg().mastodonAccessToken}`, 'Content-Type': 'application/json' }, timeout: 12_000 }
    );
    rateRecord('mastodon');
    recordEngagement('mastodon', 1);
    logger.info(`Mastodon: ${res.data?.url}`);
    return res.data?.url || true;
  } catch (err) { logger.warn(`Mastodon failed: ${err.message}`); return false; }
}

let _rToken = null; let _rExpiry = 0;
async function getRedditToken() {
  if (_rToken && Date.now() < _rExpiry) return _rToken;
  if (!cfg().redditClientId) return null;
  try {
    const res = await axios.post(
      'https://www.reddit.com/api/v1/access_token',
      `grant_type=password&username=${encodeURIComponent(cfg().redditUsername)}&password=${encodeURIComponent(cfg().redditPassword)}`,
      { auth: { username: cfg().redditClientId, password: cfg().redditClientSecret },
        headers: { 'User-Agent': `ProfitEngine/5.0 by ${cfg().contactEmail}`, 'Content-Type': 'application/x-www-form-urlencoded' }, timeout: 10_000 }
    );
    _rToken = res.data.access_token;
    _rExpiry = Date.now() + (res.data.expires_in - 60) * 1000;
    return _rToken;
  } catch { return null; }
}

async function postReddit(post) {
  const token = await getRedditToken();
  if (!token || !rateCheck('reddit')) return false;
  const sub = NICHE_SUBREDDITS[post.niche] || 'passive_income';
  try {
    await axios.post(
      'https://oauth.reddit.com/api/submit',
      new URLSearchParams({ kind: 'link', sr: sub, title: post.title.slice(0,300),
        url: `https://${cfg().siteDomain}/${post.slug || ''}`, resubmit: 'true', nsfw: 'false' }).toString(),
      { headers: { Authorization: `bearer ${token}`, 'User-Agent': `ProfitEngine/5.0 by ${cfg().contactEmail}`, 'Content-Type': 'application/x-www-form-urlencoded' }, timeout: 12_000 }
    );
    rateRecord('reddit');
    recordEngagement('reddit', 2);
    logger.info(`Reddit: r/${sub} — ${post.title.slice(0,50)}`);
    return true;
  } catch (err) { logger.warn(`Reddit failed: ${err.message}`); return false; }
}

async function postPinterest(post) {
  if (!cfg().pinterestToken || !cfg().pinterestBoardId || !rateCheck('pinterest')) return false;
  try {
    const description = await content.generateSocialCaption(post, 'pinterest');
    const res = await axios.post('https://api.pinterest.com/v5/pins',
      { board_id: cfg().pinterestBoardId, title: post.title.slice(0,100),
        description: description.slice(0,500), link: `https://${cfg().siteDomain}/${post.slug || ''}`,
        media_source: { source_type: 'image_url', url: `https://${cfg().siteDomain}/og-default.jpg` } },
      { headers: { Authorization: `Bearer ${cfg().pinterestToken}`, 'Content-Type': 'application/json' }, timeout: 15_000 }
    );
    rateRecord('pinterest');
    recordEngagement('pinterest', 1.5);
    logger.info(`Pinterest pin: ${res.data?.id}`);
    return `https://pinterest.com/pin/${res.data?.id}`;
  } catch (err) { logger.warn(`Pinterest failed: ${err.message}`); return false; }
}

async function distribute(post) {
  if (!post) return 0;
  const results = await Promise.allSettled([postMastodon(post), postReddit(post), postPinterest(post)]);
  const ok = results.filter(r => r.status === 'fulfilled' && r.value).length;
  if (ok > 0) { state.increment('totalSocial', ok); }
  logger.info(`Social: ${ok}/3 platforms — ${post.title.slice(0,40)}`);
  return ok;
}

module.exports = { distribute, postMastodon, postReddit, postPinterest };
