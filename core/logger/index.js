'use strict';
/**
 * core/logger/index.js — ProfitEngine v5.0
 * Enterprise structured logger. Per-module child loggers.
 * Sensitive value masking. Rotating file transport.
 */
const { createLogger, format, transports } = require('winston');
const path = require('path');
const fs   = require('fs');

const LOG_DIR = path.join(process.cwd(), 'logs');
fs.mkdirSync(LOG_DIR, { recursive: true });

const SENSITIVE_KEYS = new Set(['key','secret','token','password','pass','auth','credential']);

function maskValue(k, v) {
  const lk = k.toLowerCase();
  if (SENSITIVE_KEYS.has(lk) || SENSITIVE_KEYS.has(lk.replace(/[_-]/g,''))) {
    return v ? '[REDACTED]' : '(unset)';
  }
  return v;
}

function maskObject(obj) {
  if (!obj || typeof obj !== 'object') return obj;
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    out[k] = typeof v === 'object' ? maskObject(v) : maskValue(k, v);
  }
  return out;
}

const sanitize = format((info) => {
  if (info.meta)  info.meta  = maskObject(info.meta);
  if (info.error) {
    const { config: _, ...safeErr } = info.error;
    info.error = safeErr;
  }
  return info;
});

const baseLogger = createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: format.combine(
    sanitize(),
    format.timestamp({ format: 'YYYY-MM-DDTHH:mm:ss.SSSZ' }),
    format.errors({ stack: true }),
    format.json()
  ),
  transports: [
    new transports.Console({
      format: format.combine(
        format.colorize(),
        format.printf(({ timestamp, level, message, module: mod, ...rest }) => {
          const tag = mod ? `[${mod}]` : '';
          const extra = Object.keys(rest).length > 0 ? ' ' + JSON.stringify(rest) : '';
          return `${timestamp} ${level}${tag} ${message}${extra}`;
        })
      )
    }),
    new transports.File({ filename: path.join(LOG_DIR, 'error.log'),    level: 'error', maxsize: 10*1024*1024, maxFiles: 5 }),
    new transports.File({ filename: path.join(LOG_DIR, 'combined.log'),              maxsize: 20*1024*1024, maxFiles: 10 }),
  ],
  exceptionHandlers: [
    new transports.File({ filename: path.join(LOG_DIR, 'exceptions.log') })
  ],
});

function child(module) {
  return baseLogger.child({ module });
}

module.exports = { ...baseLogger, child };
