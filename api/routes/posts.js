'use strict';
const express = require('express');
const router  = express.Router();
const state   = require('../../core/state');

router.get('/',     (req, res) => res.json({ published: state.get('publishedPosts',[]).slice(-30), log: state.get('publishLog',[]).slice(-20) }));
router.get('/trends',(req,res) => res.json({ latest: state.get('latestTrends',[]), keywords: state.get('latestKeywords',[]), lastScan: state.get('lastTrendScan') }));
router.get('/revenue',(req,res) => res.json({ events: state.get('revenueEvents',[]).slice(-50), monthly: {}, allTime: {} }));
module.exports = router;
