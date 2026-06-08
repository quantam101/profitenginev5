'use strict';
/**
 * api/index.js — ProfitEngine v5.0
 * Express API server with auth, rate limiting, routes.
 */
const express   = require('express');
const path      = require('path');
const logger    = require('../core/logger').child('API');
const auth      = require('./middleware/auth');
const rateLimit = require('./middleware/rateLimit');
const statusR   = require('./routes/status');
const postsR    = require('./routes/posts');
const askR      = require('./routes/ask');
const cfg       = require('../core/config').get;

const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname, '../dashboard/public')));
app.use('/api', rateLimit(120));
app.use('/api', auth);
app.use('/api/status',  statusR);
app.use('/api/posts',   postsR);
app.use('/api/ask',     askR);
app.get('*', (req, res) => res.sendFile(path.join(__dirname, '../dashboard/public/index.html')));

function start(port) {
  const p = port || cfg().port;
  app.listen(p, () => logger.info(`API live on http://localhost:${p}`));
  return app;
}

module.exports = { app, start };
