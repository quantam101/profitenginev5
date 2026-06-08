'use strict';
const cfg = require('../../core/config').get;
module.exports = function basicAuth(req, res, next) {
  const u = cfg().dashUser, p = cfg().dashPass;
  if (!u || !p) return next();
  const h = req.headers.authorization || '';
  const [type, creds] = h.split(' ');
  if (type !== 'Basic') return res.status(401).set('WWW-Authenticate','Basic realm="ProfitEngine"').send('Auth required');
  const [user, pass] = Buffer.from(creds||'','base64').toString().split(':');
  if (user === u && pass === p) return next();
  return res.status(401).set('WWW-Authenticate','Basic realm="ProfitEngine"').send('Invalid credentials');
};
