'use strict';
/**
 * agents/affiliate/index.js — ProfitEngine v5.0
 * Tier 0 only — pure logic, zero tokens.
 * Amazon affiliate injection with product section, FTC disclosure,
 * contextual product matching, and click tracking hooks.
 */
const logger = require('../../core/logger').child('AFFILIATE');
const cfg    = require('../../core/config').get;

const PRODUCT_MAP = {
  'ring light': 'ring+light+streaming+kit', 'tripod': 'flexible+camera+tripod',
  'microphone': 'usb+condenser+microphone+podcast', 'laptop stand': 'adjustable+laptop+stand+ergonomic',
  'webcam': 'hd+webcam+1080p+streaming', 'canva pro': 'graphic+design+software',
  'web hosting': 'web+hosting+wordpress', 'hosting': 'web+hosting+beginner',
  'keyboard': 'mechanical+keyboard+wireless+rgb', 'monitor': '27+inch+monitor+4k+usb-c',
  'desk': 'electric+standing+desk+adjustable', 'chair': 'ergonomic+office+chair+lumbar',
  'headphones': 'noise+cancelling+headphones+wireless', 'printer': 'wireless+all-in-one+printer',
  'camera': '4k+vlogging+camera+kit', 'planner': 'productivity+planner+undated',
  'notebook': 'premium+hardcover+notebook+dotted', 'course': 'online+learning+subscription',
};

const FTC_DISCLOSURE = '\n\n> **Disclosure:** This post contains affiliate links. If you purchase through these links, I may earn a commission at no extra cost to you. I only recommend products I\'ve researched and believe in.\n';

function buildLink(product) {
  const tag   = cfg().amazonTag || 'alreadyhere-20';
  const query = PRODUCT_MAP[product.toLowerCase()] || encodeURIComponent(product);
  return `https://www.amazon.com/s?k=${query}&tag=${tag}&linkCode=ll2`;
}

function contextualMatch(text, products) {
  const matches = [];
  for (const product of products) {
    const escaped = product.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex   = new RegExp(`\\b${escaped}\\b`, 'gi');
    if (regex.test(text)) matches.push(product);
  }
  return matches;
}

function injectLinks(bodyText, products = []) {
  if (!bodyText) return { text: bodyText, linksInjected: 0, productsUsed: [] };
  let text = bodyText;
  let linksInjected = 0;
  const productsUsed = [];
  const allProducts  = products.length ? products : cfg().affiliateProducts;

  // Replace [AMAZON_LINK] placeholders
  text = text.replace(/\[AMAZON_LINK\]/gi, () => {
    const p = allProducts[linksInjected % allProducts.length];
    linksInjected++;
    return buildLink(p);
  });

  // Inject inline links (max 2 per product, skip existing links)
  for (const product of allProducts) {
    const escaped = product.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex   = new RegExp(`(?<!\\[|https?://\\S{0,100})(\\b${escaped}\\b)(?!\\]|\\()`, 'gi');
    let count = 0;
    text = text.replace(regex, match => {
      if (count >= 2) return match;
      count++;
      linksInjected++;
      if (!productsUsed.includes(product)) productsUsed.push(product);
      return `[${match}](${buildLink(product.toLowerCase())})`;
    });
  }

  return { text, linksInjected, productsUsed };
}

function buildProductSection(products = []) {
  const list = products.length ? products.slice(0, 5) : cfg().affiliateProducts.slice(0, 4);
  const items = list.map(p => `| **[${p}](${buildLink(p.toLowerCase())})** | Top-rated | Amazon | [View Deal →](${buildLink(p.toLowerCase())}) |`);
  return `\n\n## Recommended Products\n\n| Product | Rating | Source | Link |\n|---------|--------|--------|------|\n${items.join('\n')}\n${FTC_DISCLOSURE}`;
}

function processPost(post) {
  if (!post?.body) return post;
  const { text, linksInjected, productsUsed } = injectLinks(post.body, post.trend?.affiliateProducts);
  const withSection = text + buildProductSection(post.trend?.affiliateProducts);
  return { ...post, body: withSection, linksInjected, affiliateProductsUsed: productsUsed, ftcCompliant: true };
}

module.exports = { injectLinks, buildProductSection, buildLink, processPost, contextualMatch };
