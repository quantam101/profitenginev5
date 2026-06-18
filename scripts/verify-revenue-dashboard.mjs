#!/usr/bin/env node

/**
 * Revenue Dashboard Verification Script
 *
 * Validates that the revenue dashboard is configured correctly and returns accurate metrics.
 *
 * Usage:
 *   node scripts/verify-revenue-dashboard.mjs [api_url]
 *
 * Examples:
 *   node scripts/verify-revenue-dashboard.mjs                    # Uses localhost:3000
 *   node scripts/verify-revenue-dashboard.mjs https://prod.com   # Uses production URL
 */

import http from 'http';
import https from 'https';

const API_URL = process.argv[2] || 'http://localhost:3000';
const ENDPOINT = '/api/command/revenue';

const log = {
  info: (msg) => console.log(`[INFO] ${msg}`),
  success: (msg) => console.log(`[✓] ${msg}`),
  warn: (msg) => console.log(`[⚠] ${msg}`),
  error: (msg) => console.log(`[✗] ${msg}`),
};

async function fetchJson(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;

    client.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          reject(new Error(`Invalid JSON response: ${e.message}`));
        }
      });
    }).on('error', reject);
  });
}

function validateMetrics(metrics) {
  const errors = [];
  const warnings = [];

  // Check required fields
  const requiredFields = [
    'mrr', 'arr', 'ltv', 'churnRate', 'cogs', 'netProfitMargin',
    'totalCustomers', 'payingCustomers', 'freeCustomers',
    'tierBreakdown', 'revenueByTier', 'topCustomers', 'health'
  ];

  for (const field of requiredFields) {
    if (!(field in metrics)) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Validate numeric values
  if (typeof metrics.mrr !== 'number' || metrics.mrr < 0) {
    errors.push('MRR must be a non-negative number');
  }

  if (typeof metrics.arr !== 'number' || metrics.arr < 0) {
    errors.push('ARR must be a non-negative number');
  }

  if (typeof metrics.ltv !== 'number' || metrics.ltv < 0) {
    errors.push('LTV must be a non-negative number');
  }

  if (typeof metrics.churnRate !== 'number' || metrics.churnRate < 0 || metrics.churnRate > 100) {
    errors.push('Churn rate must be between 0-100');
  }

  if (typeof metrics.cogs !== 'number' || metrics.cogs < 0) {
    errors.push('COGS must be a non-negative number');
  }

  if (typeof metrics.netProfitMargin !== 'number' || metrics.netProfitMargin < -100 || metrics.netProfitMargin > 100) {
    errors.push('Net profit margin must be between -100 and 100');
  }

  // Validate customer counts
  if (typeof metrics.totalCustomers !== 'number' || metrics.totalCustomers < 0) {
    errors.push('Total customers must be a non-negative number');
  }

  if (metrics.payingCustomers > metrics.totalCustomers) {
    errors.push('Paying customers cannot exceed total customers');
  }

  if (metrics.payingCustomers + metrics.freeCustomers > metrics.totalCustomers) {
    warnings.push('Sum of paying + free customers exceeds total customers');
  }

  // Validate ARR = MRR * 12
  const expectedArr = metrics.mrr * 12;
  if (Math.abs(metrics.arr - expectedArr) > 0.01) {
    warnings.push(`ARR (${metrics.arr}) does not equal MRR * 12 (${expectedArr})`);
  }

  // Validate LTV calculation
  const avgMonthlyRevenue = metrics.payingCustomers > 0 ? metrics.mrr / metrics.payingCustomers : 0;
  const expectedLtv = avgMonthlyRevenue * 24;
  if (Math.abs(metrics.ltv - expectedLtv) > 1) {
    warnings.push(`LTV (${metrics.ltv}) does not equal avg monthly revenue * 24 (${expectedLtv})`);
  }

  // Validate tier breakdown
  const totalTierCustomers = Object.values(metrics.tierBreakdown).reduce((a, b) => a + b, 0);
  if (totalTierCustomers !== metrics.totalCustomers) {
    warnings.push(`Tier breakdown total (${totalTierCustomers}) does not match total customers (${metrics.totalCustomers})`);
  }

  // Validate revenue by tier
  const totalTierRevenue = Object.values(metrics.revenueByTier).reduce((a, b) => a + b, 0);
  if (Math.abs(totalTierRevenue - metrics.mrr) > 0.01) {
    warnings.push(`Revenue by tier total (${totalTierRevenue}) does not match MRR (${metrics.mrr})`);
  }

  // Validate health data
  if (!metrics.health || typeof metrics.health !== 'object') {
    errors.push('Health section must be an object');
  } else {
    if (!metrics.health.dataQuality) {
      errors.push('Health data must include dataQuality');
    }
    if (!metrics.health.lastUpdate) {
      errors.push('Health data must include lastUpdate');
    }
  }

  return { errors, warnings };
}

async function main() {
  const fullUrl = `${API_URL}${ENDPOINT}`;

  log.info(`Verifying Revenue Dashboard`);
  log.info(`API URL: ${fullUrl}`);
  log.info('---');

  try {
    // 1. Fetch metrics
    log.info('Fetching metrics from API...');
    const response = await fetchJson(fullUrl);

    if (response.status !== 200) {
      log.error(`API returned status ${response.status}`);
      process.exit(1);
    }

    log.success(`API responded with status 200`);

    const metrics = response.data;

    // 2. Validate metrics
    log.info('Validating metric structure and values...');
    const { errors, warnings } = validateMetrics(metrics);

    if (errors.length > 0) {
      log.error(`Found ${errors.length} validation errors:`);
      errors.forEach(e => log.error(`  - ${e}`));
      process.exit(1);
    } else {
      log.success('All validations passed');
    }

    if (warnings.length > 0) {
      log.warn(`Found ${warnings.length} warnings:`);
      warnings.forEach(w => log.warn(`  - ${w}`));
    }

    // 3. Display summary
    log.info('---');
    log.info('Metrics Summary:');
    log.info(`  MRR: $${metrics.mrr.toFixed(2)}`);
    log.info(`  ARR: $${metrics.arr.toFixed(2)}`);
    log.info(`  LTV: $${metrics.ltv.toFixed(2)}`);
    log.info(`  Churn Rate: ${metrics.churnRate.toFixed(2)}%`);
    log.info(`  COGS: $${metrics.cogs.toFixed(2)}`);
    log.info(`  Net Profit Margin: ${metrics.netProfitMargin.toFixed(2)}%`);
    log.info(`  Total Customers: ${metrics.totalCustomers}`);
    log.info(`  Paying Customers: ${metrics.payingCustomers}`);
    log.info(`  Free Customers: ${metrics.freeCustomers}`);

    // 4. Tier breakdown
    log.info('---');
    log.info('Tier Breakdown:');
    log.info(`  Free: ${metrics.tierBreakdown.free} customers (${metrics.revenueByTier.free > 0 ? '$' + metrics.revenueByTier.free.toFixed(2) : '$0.00'})`);
    log.info(`  Hybrid: ${metrics.tierBreakdown.hybrid} customers ($${metrics.revenueByTier.hybrid.toFixed(2)})`);
    log.info(`  White Label: ${metrics.tierBreakdown.whiteLable} customers ($${metrics.revenueByTier.whiteLable.toFixed(2)})`);
    log.info(`  Enterprise: ${metrics.tierBreakdown.enterprise} customers ($${metrics.revenueByTier.enterprise.toFixed(2)})`);

    // 5. Top customers
    if (metrics.topCustomers && metrics.topCustomers.length > 0) {
      log.info('---');
      log.info(`Top ${Math.min(3, metrics.topCustomers.length)} Customers:`);
      metrics.topCustomers.slice(0, 3).forEach((customer, i) => {
        log.info(`  ${i + 1}. ${customer.email.split('@')[0]}@... (${customer.tier}): $${customer.monthlyRevenue.toFixed(2)}/mo`);
      });
    }

    // 6. Health status
    log.info('---');
    log.info('Health Status:');
    log.info(`  Data Quality: ${metrics.health.dataQuality}`);
    log.info(`  Records Processed: ${metrics.health.recordsProcessed}`);
    log.info(`  Last Updated: ${new Date(metrics.health.lastUpdate).toLocaleString()}`);

    log.info('---');
    log.success('Revenue Dashboard verification complete!');
    process.exit(0);

  } catch (error) {
    log.error(`Verification failed: ${error.message}`);

    if (error.message.includes('ECONNREFUSED')) {
      log.error(`Cannot connect to ${API_URL}`);
      log.error(`Make sure the development server is running: npm run dev`);
    }

    process.exit(1);
  }
}

main();
