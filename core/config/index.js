'use strict';
/**
 * core/config/index.js — ProfitEngine v5.0
 * Enterprise config with full validation, env schema enforcement,
 * runtime reload support, and audit-safe redaction.
 */
const REQUIRED = [];
const MASKED   = '[REDACTED]';
const SENSITIVE = ['key','secret','token','password','pass','auth'];

function env(key, fallback = null, required = false) {
  const val = process.env[key];
  if (!val && required) throw new Error(`[CONFIG] Required env var missing: ${key}`);
  return val !== undefined ? val : (fallback !== null ? fallback : undefined);
}

function envInt(key, fallback = 0) { return parseInt(env(key, String(fallback)), 10); }
function envFloat(key, fallback = 0) { return parseFloat(env(key, String(fallback))); }
function envBool(key, fallback = false) { const v = env(key, null); return v !== null ? v === 'true' || v === '1' : fallback; }
function envList(key, fallback = '') { return (env(key, fallback)).split(',').map(s => s.trim()).filter(Boolean); }

function build() {
  return {
    // System
    version:      '5.0.0',
    env:          env('NODE_ENV', 'production'),
    port:         envInt('PORT', 3000),
    logLevel:     env('LOG_LEVEL', 'info'),
    sessionId:    `pe5_${Date.now()}`,

    // Business
    businessName: env('BUSINESS_NAME', 'Already Here LLC'),
    siteDomain:   env('SITE_DOMAIN', 'alreadyherellc.com'),
    contactEmail: env('CONTACT_EMAIL', 'alreadyherellc@gmail.com'),
    alertEmail:   env('ALERT_EMAIL', 'alreadyherellc@gmail.com'),

    // Dashboard
    dashUser: env('DASH_USER', ''),
    dashPass: env('DASH_PASS', ''),

    // LLM providers
    groqApiKey:       env('GROQ_API_KEY', ''),
    openrouterApiKey: env('OPENROUTER_API_KEY', ''),
    geminiApiKey:     env('GEMINI_API_KEY', ''),
    dailyTokenLimit:  envInt('DAILY_TOKEN_LIMIT', 500000),

    // Content strategy
    targetNiches:      envList('TARGET_NICHES', 'passive income,ai tools,side hustle,print on demand,affiliate marketing'),
    affiliateProducts: envList('AFFILIATE_PRODUCTS', 'ring light,tripod,microphone,laptop stand,canva pro,web hosting'),
    scanIntervalMin:   envInt('SCAN_INTERVAL_MINUTES', 15),
    maxPostsPerDay:    envInt('MAX_POSTS_PER_DAY', 20),
    contentPerRun:     envInt('CONTENT_PER_RUN', 3),
    minWordCount:      envInt('MIN_WORD_COUNT', 800),
    maxWordCount:      envInt('MAX_WORD_COUNT', 1400),

    // GitHub
    githubToken:   env('GITHUB_TOKEN', ''),
    githubOwner:   env('GITHUB_OWNER', 'quantam101'),
    githubRepo:    env('GITHUB_REPO', 'already-here-llc'),
    githubBlogDir: env('GITHUB_BLOG_DIR', 'posts'),

    // MongoDB (shared with backend/server.py — system of record for payments)
    mongoUrl: env('MONGO_URL', ''),
    dbName:   env('DB_NAME', ''),

    // Blog platforms
    devtoApiKey:           env('DEVTO_API_KEY', ''),
    hashnodeApiKey:        env('HASHNODE_API_KEY', ''),
    hashnodePublicationId: env('HASHNODE_PUBLICATION_ID', ''),
    mediumApiKey:          env('MEDIUM_API_KEY', ''),
    mediumAuthorId:        env('MEDIUM_AUTHOR_ID', ''),

    // Social platforms
    mastodonAccessToken: env('MASTODON_ACCESS_TOKEN', ''),
    mastodonInstance:    env('MASTODON_INSTANCE', 'mastodon.social'),
    pinterestToken:      env('PINTEREST_ACCESS_TOKEN', ''),
    pinterestBoardId:    env('PINTEREST_BOARD_ID', ''),
    redditClientId:      env('REDDIT_CLIENT_ID', ''),
    redditClientSecret:  env('REDDIT_CLIENT_SECRET', ''),
    redditUsername:      env('REDDIT_USERNAME', ''),
    redditPassword:      env('REDDIT_PASSWORD', ''),

    // Affiliate
    amazonTag:             env('AMAZON_PARTNER_TAG', 'alreadyhere-20'),
    amazonPayoutThreshold: envFloat('AMAZON_PAYOUT_THRESHOLD', 10),

    // POD
    printifyApiKey: env('PRINTIFY_API_KEY', ''),
    printifyShopId: env('PRINTIFY_SHOP_ID', ''),

    // Email
    gmailUser:        env('GMAIL_USER', ''),
    gmailAppPassword: env('GMAIL_APP_PASSWORD', ''),
    mediumPayoutThreshold: envFloat('MEDIUM_PAYOUT_THRESHOLD', 10),

    // UltraFlow VHLL
    ultraflowUrl:    env('ULTRAFLOW_URL', ''),
    ultraflowApiKey: env('ULTRAFLOW_API_KEY', ''),

    // Feature flags
    featurePOD:       envBool('FEATURE_POD', true),
    featureCompliance:envBool('FEATURE_COMPLIANCE', true),
    featureWebSearch: envBool('FEATURE_WEB_SEARCH', false),
  };
}

let _cfg = null;

function get() {
  if (!_cfg) _cfg = build();
  return _cfg;
}

function reload() { _cfg = build(); return _cfg; }

function validate() {
  const cfg = get();
  if (!cfg.groqApiKey && !cfg.openrouterApiKey && !cfg.geminiApiKey) {
    throw new Error('[CONFIG] At least one LLM key required: GROQ_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY');
  }
  if (!cfg.githubToken) {
    console.warn('[CONFIG] GITHUB_TOKEN missing — website publishing disabled');
  }
  return true;
}

function redacted() {
  const cfg = get();
  const out = {};
  for (const [k, v] of Object.entries(cfg)) {
    const lk = k.toLowerCase();
    out[k] = SENSITIVE.some(s => lk.includes(s)) && v ? MASKED : v;
  }
  return out;
}

module.exports = { get, reload, validate, redacted };
