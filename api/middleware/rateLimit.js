'use strict';
const hits = new Map();
module.exports = function rateLimit(maxPerMin = 60) {
  return (req, res, next) => {
    const key = req.ip || 'unknown';
    const now = Date.now();
    const win = hits.get(key) || [];
    const recent = win.filter(t => now - t < 60_000);
    recent.push(now);
    hits.set(key, recent);
    if (recent.length > maxPerMin) return res.status(429).json({ error: 'Rate limit exceeded' });
    next();
  };
};
