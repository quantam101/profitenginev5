'use strict';
/**
 * core/mongo/index.js — ProfitEngine v5.0
 * Thin shared MongoDB client (same MONGO_URL/DB_NAME as backend/server.py),
 * used to read system-of-record collections like payment_transactions
 * directly rather than relaying events through a second store.
 */
const { MongoClient } = require('mongodb');
const logger = require('../logger').child('MONGO');
const cfg    = require('../config').get;

let _client = null;
let _db     = null;

async function getDb() {
  const { mongoUrl, dbName } = cfg();
  if (!mongoUrl || !dbName) return null;
  if (_db) return _db;
  try {
    _client = new MongoClient(mongoUrl, { serverSelectionTimeoutMS: 5000 });
    await _client.connect();
    _db = _client.db(dbName);
    logger.info(`Connected to MongoDB (${dbName})`);
    return _db;
  } catch (err) {
    logger.warn(`MongoDB connection failed: ${err.message}`);
    _client = null;
    _db = null;
    return null;
  }
}

module.exports = { getDb };
