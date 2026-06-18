/**
 * Trading Report Generator
 *
 * Generates PDF reports from trading data
 * - Performance summaries with charts
 * - Tax reporting data
 * - Strategy breakdown analysis
 * - Monthly performance tables
 */

import { createWriteStream } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import { randomBytes } from 'crypto';

export interface TradeRecord {
  id: number;
  userId: number;
  date: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  duration: number; // days held
  strategy?: string;
  tags?: string;
}

export interface DailyPerformance {
  date: string;
  trades: number;
  wins: number;
  losses: number;
  winRate: number;
  pnlDollars: number;
  pnlPercent: number;
  balance: number;
}

export interface MonthlyPerformance {
  month: string;
  trades: number;
  wins: number;
  losses: number;
  winRate: number;
  totalPnl: number;
  totalPnlPercent: number;
}

export interface TaxReportData {
  shortTermGains: number; // < 1 year
  longTermGains: number; // >= 1 year
  totalGains: number;
  totalLosses: number;
  netGains: number;
  washSales: Array<{
    date: string;
    symbol: string;
    loss: number;
    repurchaseDate: string;
  }>;
  exportDate: string;
}

export interface ReportConfig {
  userId: number;
  username: string;
  email: string;
  startDate: string;
  endDate: string;
  dailyPerformance: DailyPerformance[];
  monthlyPerformance: MonthlyPerformance[];
  trades: TradeRecord[];
  taxData: TaxReportData;
  summary: {
    totalTrades: number;
    totalWins: number;
    totalLosses: number;
    overallWinRate: number;
    totalPnlDollars: number;
    totalPnlPercent: number;
    bestTrade: TradeRecord;
    worstTrade: TradeRecord;
    averageTrade: number;
    maxDrawdown: number;
  };
}

/**
 * HTML-based PDF generator (can be server-rendered or sent to browser)
 * Returns HTML string that can be converted to PDF using puppeteer, pdfkit, or sent to client
 */
export function generateTradingReportHTML(config: ReportConfig): string {
  const formatCurrency = (value: number) => {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return formatter.format(value);
  };

  const formatPercent = (value: number) => {
    return (Math.round(value * 100) / 100).toFixed(2) + '%';
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Calculate monthly data for chart
  const monthlyLabels = config.monthlyPerformance.map((m) => m.month);
  const monthlyPnL = config.monthlyPerformance.map((m) => m.totalPnl);
  const monthlyWinRate = config.monthlyPerformance.map((m) => m.winRate);

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Trading Report - ${config.username}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #1f2937;
      line-height: 1.6;
    }

    .page {
      page-break-after: always;
      padding: 40px;
      min-height: 297mm;
    }

    .cover-page {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      min-height: 297mm;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      text-align: center;
    }

    .cover-page h1 {
      font-size: 3em;
      margin-bottom: 20px;
      font-weight: 700;
    }

    .cover-page .subtitle {
      font-size: 1.5em;
      margin-bottom: 40px;
      opacity: 0.95;
    }

    .cover-page .info {
      font-size: 1em;
      margin-top: 80px;
      line-height: 2;
    }

    .cover-page .info p {
      margin: 10px 0;
    }

    .section-title {
      font-size: 2em;
      font-weight: 700;
      margin: 30px 0 20px 0;
      color: #1f2937;
      border-bottom: 3px solid #667eea;
      padding-bottom: 10px;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
      margin: 20px 0;
    }

    .metric-card {
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 20px;
      background: #f9fafb;
    }

    .metric-label {
      font-size: 0.9em;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }

    .metric-value {
      font-size: 1.8em;
      font-weight: 700;
      color: #1f2937;
    }

    .metric-positive {
      color: #059669;
    }

    .metric-negative {
      color: #dc2626;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 0.9em;
    }

    thead {
      background: #f3f4f6;
      border-bottom: 2px solid #e5e7eb;
    }

    th {
      padding: 12px;
      text-align: left;
      font-weight: 600;
      color: #374151;
    }

    td {
      padding: 12px;
      border-bottom: 1px solid #e5e7eb;
    }

    tbody tr:nth-child(even) {
      background: #f9fafb;
    }

    .text-right {
      text-align: right;
    }

    .text-center {
      text-align: center;
    }

    .positive {
      color: #059669;
      font-weight: 600;
    }

    .negative {
      color: #dc2626;
      font-weight: 600;
    }

    .footer {
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #e5e7eb;
      font-size: 0.8em;
      color: #6b7280;
      text-align: center;
    }

    .two-column {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
      margin: 20px 0;
    }

    .chart-placeholder {
      border: 2px dashed #e5e7eb;
      border-radius: 8px;
      padding: 40px;
      text-align: center;
      color: #9ca3af;
      background: #f9fafb;
      margin: 20px 0;
    }

    .highlight {
      background: #fef3c7;
      padding: 2px 6px;
      border-radius: 4px;
    }

    @page {
      size: A4;
      margin: 0;
    }

    @media print {
      body { background: white; }
      .page { page-break-after: always; }
    }
  </style>
</head>
<body>
  <!-- Cover Page -->
  <div class="page cover-page">
    <h1>Trading Report</h1>
    <p class="subtitle">Performance Analysis & Tax Reporting</p>
    <div class="info">
      <p><strong>${config.username}</strong></p>
      <p>${config.email}</p>
      <p style="margin-top: 20px; font-size: 0.9em;">
        Period: ${formatDate(config.startDate)} to ${formatDate(config.endDate)}
      </p>
      <p style="font-size: 0.9em;">
        Generated: ${formatDate(new Date().toISOString())}
      </p>
    </div>
  </div>

  <!-- Executive Summary -->
  <div class="page">
    <h2 class="section-title">Account Summary</h2>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">Total Trades</div>
        <div class="metric-value">${config.summary.totalTrades}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Overall Win Rate</div>
        <div class="metric-value ${config.summary.overallWinRate >= 50 ? 'metric-positive' : 'metric-negative'}">
          ${formatPercent(config.summary.overallWinRate)}
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Total P&L ($)</div>
        <div class="metric-value ${config.summary.totalPnlDollars >= 0 ? 'metric-positive' : 'metric-negative'}">
          ${formatCurrency(config.summary.totalPnlDollars)}
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Total P&L (%)</div>
        <div class="metric-value ${config.summary.totalPnlPercent >= 0 ? 'metric-positive' : 'metric-negative'}">
          ${formatPercent(config.summary.totalPnlPercent)}
        </div>
      </div>
    </div>

    <h3 style="margin-top: 30px; margin-bottom: 15px; color: #374151;">Key Metrics</h3>
    <table>
      <tr>
        <td style="width: 50%;">Winning Trades</td>
        <td class="text-right"><strong>${config.summary.totalWins}</strong></td>
      </tr>
      <tr>
        <td>Losing Trades</td>
        <td class="text-right"><strong>${config.summary.totalLosses}</strong></td>
      </tr>
      <tr>
        <td>Best Trade</td>
        <td class="text-right positive">${formatCurrency(config.summary.bestTrade.pnl)}</td>
      </tr>
      <tr>
        <td>Worst Trade</td>
        <td class="text-right negative">${formatCurrency(config.summary.worstTrade.pnl)}</td>
      </tr>
      <tr>
        <td>Average Trade P&L</td>
        <td class="text-right">${formatCurrency(config.summary.averageTrade)}</td>
      </tr>
      <tr>
        <td>Maximum Drawdown</td>
        <td class="text-right negative">${formatPercent(config.summary.maxDrawdown)}</td>
      </tr>
    </table>

    <div class="footer">
      <p>This report is for informational purposes only and does not constitute investment advice.</p>
    </div>
  </div>

  <!-- Monthly Performance -->
  <div class="page">
    <h2 class="section-title">Monthly Performance</h2>

    <table>
      <thead>
        <tr>
          <th>Month</th>
          <th class="text-center">Trades</th>
          <th class="text-center">W/L</th>
          <th class="text-center">Win Rate</th>
          <th class="text-right">P&L ($)</th>
          <th class="text-right">P&L (%)</th>
        </tr>
      </thead>
      <tbody>
        ${config.monthlyPerformance
          .map(
            (month) => `
        <tr>
          <td><strong>${month.month}</strong></td>
          <td class="text-center">${month.trades}</td>
          <td class="text-center">${month.wins}/${month.losses}</td>
          <td class="text-center">${formatPercent(month.winRate)}</td>
          <td class="text-right ${month.totalPnl >= 0 ? 'positive' : 'negative'}">
            ${formatCurrency(month.totalPnl)}
          </td>
          <td class="text-right ${month.totalPnlPercent >= 0 ? 'positive' : 'negative'}">
            ${formatPercent(month.totalPnlPercent)}
          </td>
        </tr>
        `
          )
          .join('')}
      </tbody>
    </table>

    <div class="chart-placeholder">
      <strong>Monthly P&L Chart</strong><br>
      <small>Data: ${monthlyLabels.join(', ')}</small><br>
      <small>P&L Values: ${monthlyPnL.map((v) => formatCurrency(v)).join(', ')}</small>
    </div>

    <div class="footer">
      <p>
        Use external charting tools or embed interactive charts for visual analysis.
        This PDF provides data summaries and tables for comprehensive reporting.
      </p>
    </div>
  </div>

  <!-- Tax Reporting -->
  <div class="page">
    <h2 class="section-title">Tax Reporting Data</h2>

    <h3 style="margin-top: 20px; margin-bottom: 15px; color: #374151;">Capital Gains Summary</h3>
    <table>
      <tr>
        <td style="width: 50%;">Short-Term Gains (< 1 year)</td>
        <td class="text-right positive">${formatCurrency(config.taxData.shortTermGains)}</td>
      </tr>
      <tr>
        <td>Long-Term Gains (≥ 1 year)</td>
        <td class="text-right positive">${formatCurrency(config.taxData.longTermGains)}</td>
      </tr>
      <tr style="background: #f3f4f6; font-weight: 600;">
        <td>Total Gains</td>
        <td class="text-right">${formatCurrency(config.taxData.totalGains)}</td>
      </tr>
      <tr>
        <td>Total Losses</td>
        <td class="text-right negative">${formatCurrency(config.taxData.totalLosses)}</td>
      </tr>
      <tr style="background: #f3f4f6; font-weight: 600; border-top: 2px solid #e5e7eb;">
        <td>Net Capital Gains/(Losses)</td>
        <td class="text-right ${config.taxData.netGains >= 0 ? 'positive' : 'negative'}">
          ${formatCurrency(config.taxData.netGains)}
        </td>
      </tr>
    </table>

    ${
      config.taxData.washSales.length > 0
        ? `
    <h3 style="margin-top: 30px; margin-bottom: 15px; color: #374151;">Wash Sale Transactions</h3>
    <p style="color: #6b7280; font-size: 0.9em; margin-bottom: 10px;">
      For tax purposes, ensure you adjust cost basis for identified wash sales:
    </p>
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Sale Date</th>
          <th>Loss Amount</th>
          <th>Repurchase Date</th>
        </tr>
      </thead>
      <tbody>
        ${config.taxData.washSales
          .map(
            (ws) => `
        <tr>
          <td>${ws.symbol}</td>
          <td>${formatDate(ws.date)}</td>
          <td class="text-right negative">${formatCurrency(ws.loss)}</td>
          <td>${formatDate(ws.repurchaseDate)}</td>
        </tr>
        `
          )
          .join('')}
      </tbody>
    </table>
    `
        : `
    <div style="background: #f9fafb; border-left: 4px solid #059669; padding: 15px; margin-top: 20px; border-radius: 4px;">
      <p style="color: #059669; font-weight: 600; margin: 0;">No wash sales detected</p>
      <p style="color: #6b7280; font-size: 0.9em; margin: 5px 0 0 0;">
        Your trading activity does not contain identified wash sales.
      </p>
    </div>
    `
    }

    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px; border-radius: 4px;">
      <p style="font-weight: 600; margin: 0;">Important Tax Notice</p>
      <p style="font-size: 0.85em; margin: 5px 0 0 0; color: #78350f;">
        This report provides a summary of your trading activity for tax purposes.
        Please consult with a tax professional to ensure proper reporting and compliance.
        Data accuracy depends on complete trade logging in the platform.
      </p>
    </div>

    <div class="footer">
      <p>Report generated on ${formatDate(new Date().toISOString())}</p>
    </div>
  </div>

  <!-- Trade Details -->
  <div class="page">
    <h2 class="section-title">Trade-by-Trade Details</h2>

    <p style="color: #6b7280; font-size: 0.9em; margin-bottom: 15px;">
      ${config.trades.length} trades recorded from ${formatDate(config.startDate)} to ${formatDate(config.endDate)}
    </p>

    <table style="font-size: 0.85em;">
      <thead>
        <tr>
          <th>Date</th>
          <th>Symbol</th>
          <th>Side</th>
          <th class="text-right">Entry</th>
          <th class="text-right">Exit</th>
          <th class="text-right">P&L</th>
          <th class="text-right">Return %</th>
          <th class="text-center">Days</th>
        </tr>
      </thead>
      <tbody>
        ${config.trades
          .slice(0, 30)
          .map(
            (trade) => `
        <tr>
          <td>${formatDate(trade.date)}</td>
          <td><strong>${trade.symbol}</strong></td>
          <td>${trade.side}</td>
          <td class="text-right">${formatCurrency(trade.entryPrice)}</td>
          <td class="text-right">${formatCurrency(trade.exitPrice)}</td>
          <td class="text-right ${trade.pnl >= 0 ? 'positive' : 'negative'}">
            ${formatCurrency(trade.pnl)}
          </td>
          <td class="text-right ${trade.pnlPercent >= 0 ? 'positive' : 'negative'}">
            ${formatPercent(trade.pnlPercent)}
          </td>
          <td class="text-center">${trade.duration}</td>
        </tr>
        `
          )
          .join('')}
      </tbody>
    </table>

    ${
      config.trades.length > 30
        ? `
    <p style="color: #6b7280; font-size: 0.85em; margin-top: 15px; font-style: italic;">
      Showing first 30 of ${config.trades.length} trades. Download CSV for complete trade history.
    </p>
    `
        : ''
    }

    <div class="footer">
      <p>Use the CSV export for filtering, sorting, and detailed analysis of all trades.</p>
    </div>
  </div>
</body>
</html>
  `.trim();
}

/**
 * Convert trading data to CSV format
 */
export function generateCSVExport(
  trades: TradeRecord[],
  config: {
    userId: number;
    username: string;
    email: string;
    startDate: string;
    endDate: string;
  }
): string {
  const headers = [
    'Date',
    'Symbol',
    'Side',
    'Entry Price',
    'Exit Price',
    'Quantity',
    'P&L ($)',
    'P&L (%)',
    'Days Held',
    'Strategy',
    'Tags',
  ];

  const rows = trades.map((trade) => [
    trade.date,
    trade.symbol,
    trade.side,
    trade.entryPrice.toFixed(2),
    trade.exitPrice.toFixed(2),
    trade.quantity.toString(),
    trade.pnl.toFixed(2),
    trade.pnlPercent.toFixed(2),
    trade.duration.toString(),
    trade.strategy || '',
    trade.tags || '',
  ]);

  const csvContent = [headers, ...rows].map((row) =>
    row.map((cell) => {
      // Escape quotes and wrap in quotes if contains comma
      const cellStr = String(cell);
      if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
        return '"' + cellStr.replace(/"/g, '""') + '"';
      }
      return cellStr;
    })
  );

  const header = `# Trading History Export
# User: ${config.username} (${config.email})
# Period: ${config.startDate} to ${config.endDate}
# Generated: ${new Date().toISOString()}
# Total Trades: ${trades.length}
`;

  return header + '\n' + csvContent.map((row) => row.join(',')).join('\n');
}

/**
 * Generate tax-focused CSV export
 */
export function generateTaxCSVExport(trades: TradeRecord[]): string {
  const headers = [
    'Date',
    'Symbol',
    'Side',
    'Entry Price',
    'Exit Price',
    'Quantity',
    'Cost Basis',
    'Proceeds',
    'Gain/Loss',
    'Holding Period (Days)',
    'Term (ST/LT)',
  ];

  const rows = trades.map((trade) => {
    const costBasis = trade.entryPrice * trade.quantity;
    const proceeds = trade.exitPrice * trade.quantity;
    const holdingDays = trade.duration;
    const term = holdingDays >= 365 ? 'LT' : 'ST';

    return [
      trade.date,
      trade.symbol,
      trade.side,
      trade.entryPrice.toFixed(2),
      trade.exitPrice.toFixed(2),
      trade.quantity.toString(),
      costBasis.toFixed(2),
      proceeds.toFixed(2),
      trade.pnl.toFixed(2),
      holdingDays.toString(),
      term,
    ];
  });

  const csvContent = [headers, ...rows]
    .map((row) =>
      row.map((cell) => {
        const cellStr = String(cell);
        if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
          return '"' + cellStr.replace(/"/g, '""') + '"';
        }
        return cellStr;
      })
    )
    .join('\n');

  return csvContent;
}

/**
 * Get temp file path for generated report
 */
export function getTempReportPath(userId: number, format: 'pdf' | 'csv'): string {
  const filename = `trading-report-${userId}-${Date.now()}.${format === 'pdf' ? 'html' : 'csv'}`;
  return join(tmpdir(), filename);
}
