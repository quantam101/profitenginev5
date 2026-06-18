#!/usr/bin/env node

/**
 * Export Trades Script
 *
 * CLI utility to generate and download trading exports programmatically
 *
 * Usage:
 *   node scripts/export-trades.mjs --format csv --user-id 1 --start-date 2024-01-01 --end-date 2024-12-31
 *   node scripts/export-trades.mjs --help
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    format: 'csv',
    dataType: 'all',
    output: null,
    userId: null,
    startDate: null,
    endDate: null,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const value = args[i + 1];

    switch (arg) {
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
      case '--format':
      case '-f':
        options.format = value;
        i++;
        break;
      case '--data-type':
      case '-t':
        options.dataType = value;
        i++;
        break;
      case '--output':
      case '-o':
        options.output = value;
        i++;
        break;
      case '--user-id':
      case '-u':
        options.userId = value;
        i++;
        break;
      case '--start-date':
      case '-s':
        options.startDate = value;
        i++;
        break;
      case '--end-date':
      case '-e':
        options.endDate = value;
        i++;
        break;
    }
  }

  return options;
}

// Print help message
function printHelp() {
  console.log(`
Export Trades CLI
=================

Generate and download trading exports from ProfitEngine

USAGE:
  node scripts/export-trades.mjs [OPTIONS]

OPTIONS:
  --format, -f        Export format (csv, pdf, tax-csv)
                      Default: csv

  --data-type, -t     Data type to export
                      (all, summary, trades, tax)
                      Default: all

  --user-id, -u       User ID (required for CLI mode)

  --start-date, -s    Start date in YYYY-MM-DD format
                      Default: 90 days ago

  --end-date, -e      End date in YYYY-MM-DD format
                      Default: today

  --output, -o        Output file path
                      Default: trading-export-[timestamp].[ext]

  --help, -h          Show this help message

EXAMPLES:
  # Export last 90 days as CSV
  node scripts/export-trades.mjs --user-id 123

  # Export specific date range as PDF
  node scripts/export-trades.mjs \\
    --format pdf \\
    --user-id 123 \\
    --start-date 2024-01-01 \\
    --end-date 2024-12-31

  # Export tax data to specific file
  node scripts/export-trades.mjs \\
    --format tax-csv \\
    --data-type tax \\
    --user-id 123 \\
    --output ~/Documents/tax-export-2024.csv

ENVIRONMENT VARIABLES:
  PROFITENGINE_API=http://localhost:3000
  USER_EMAIL=user@example.com
  AUTH_TOKEN=your-api-token

NOTES:
  - This script requires authentication
  - Date range defaults to last 90 days if not specified
  - Output file extensions are added automatically
  - Large exports may take up to 5 seconds to generate
  `);
}

// Validate options
function validateOptions(options) {
  const validFormats = ['csv', 'pdf', 'tax-csv'];
  const validDataTypes = ['all', 'summary', 'trades', 'tax'];

  if (!validFormats.includes(options.format)) {
    console.error(`Error: Invalid format '${options.format}'. Valid options: ${validFormats.join(', ')}`);
    process.exit(1);
  }

  if (!validDataTypes.includes(options.dataType)) {
    console.error(`Error: Invalid data type '${options.dataType}'. Valid options: ${validDataTypes.join(', ')}`);
    process.exit(1);
  }

  // Set default dates if not provided
  if (!options.endDate) {
    const today = new Date();
    options.endDate = today.toISOString().split('T')[0];
  }

  if (!options.startDate) {
    const date = new Date();
    date.setDate(date.getDate() - 90);
    options.startDate = date.toISOString().split('T')[0];
  }

  // Validate date format
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRegex.test(options.startDate)) {
    console.error('Error: Start date must be in YYYY-MM-DD format');
    process.exit(1);
  }
  if (!dateRegex.test(options.endDate)) {
    console.error('Error: End date must be in YYYY-MM-DD format');
    process.exit(1);
  }

  // Validate date range
  if (new Date(options.startDate) > new Date(options.endDate)) {
    console.error('Error: Start date must be before end date');
    process.exit(1);
  }

  return options;
}

// Generate output filename
function getOutputFilename(options) {
  if (options.output) {
    return options.output;
  }

  const timestamp = Date.now();
  const ext = options.format === 'pdf' ? 'html' : 'csv';
  return `trading-export-${timestamp}.${ext}`;
}

// Fetch export from API
async function fetchExport(options) {
  const apiUrl = process.env.PROFITENGINE_API || 'http://localhost:3000';
  const endpoint = `${apiUrl}/api/trading/export`;

  const requestBody = {
    format: options.format,
    startDate: options.startDate,
    endDate: options.endDate,
    dataType: options.dataType,
  };

  console.log(`Generating ${options.format} export...`);
  console.log(`  Format: ${options.format}`);
  console.log(`  Date Range: ${options.startDate} to ${options.endDate}`);
  console.log(`  Data Type: ${options.dataType}`);

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.AUTH_TOKEN || 'default-token'}`,
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `API error: ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    return Buffer.from(buffer);
  } catch (error) {
    console.error(`Error: Failed to fetch export: ${error.message}`);
    process.exit(1);
  }
}

// Save export to file
async function saveExport(filename, data) {
  try {
    const filepath = path.resolve(filename);
    const dir = path.dirname(filepath);

    // Create directory if it doesn't exist
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Write file
    fs.writeFileSync(filepath, data);

    console.log(`✓ Export saved to: ${filepath}`);
    console.log(`  Size: ${(data.length / 1024).toFixed(2)} KB`);

    return filepath;
  } catch (error) {
    console.error(`Error: Failed to save export: ${error.message}`);
    process.exit(1);
  }
}

// Main execution
async function main() {
  const options = parseArgs();
  validateOptions(options);

  const filename = getOutputFilename(options);
  const data = await fetchExport(options);
  const filepath = await saveExport(filename, data);

  console.log(`\n✓ Export completed successfully!`);
  console.log(`  File: ${filepath}`);
  console.log(`  Format: ${options.format}`);
  console.log(`  Period: ${options.startDate} to ${options.endDate}`);
}

// Run if called directly
main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exit(1);
});
