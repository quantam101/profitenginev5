#!/usr/bin/env node
/**
 * scripts/monetization_report_generator.js
 * Generate comprehensive monetization reports from test results
 * Usage: node scripts/monetization_report_generator.js [--article <path>] [--output <path>]
 */

const fs = require('fs');
const path = require('path');
const monetization = require('../agents/monetization');

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const result = { articlePath: null, outputPath: null };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--article' && i + 1 < args.length) {
      result.articlePath = args[i + 1];
      i++;
    } else if (args[i] === '--output' && i + 1 < args.length) {
      result.outputPath = args[i + 1];
      i++;
    }
  }

  return result;
}

// Load article from file
function loadArticle(filePath) {
  try {
    if (filePath.endsWith('.md')) {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      const title = lines[0]?.replace(/^#\s+/, '').trim() || 'Untitled';
      return {
        title,
        content,
        topic: 'General',
        filePath
      };
    } else if (filePath.endsWith('.json')) {
      const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      return data;
    }
  } catch (err) {
    console.error(`Failed to load article: ${err.message}`);
    return null;
  }
}

// Generate HTML report
function generateHTMLReport(testResult) {
  const report = testResult.report;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Monetization Report - ${report.articleMetadata.title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #333;
      padding: 40px 20px;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 40px;
      text-align: center;
    }
    header h1 {
      font-size: 2.5em;
      margin-bottom: 10px;
    }
    header p {
      font-size: 1.2em;
      opacity: 0.9;
    }
    .content {
      padding: 40px;
    }
    .section {
      margin-bottom: 40px;
      padding-bottom: 40px;
      border-bottom: 2px solid #f0f0f0;
    }
    .section:last-child {
      border-bottom: none;
    }
    h2 {
      color: #667eea;
      font-size: 1.8em;
      margin-bottom: 20px;
      border-left: 4px solid #667eea;
      padding-left: 15px;
    }
    h3 {
      color: #764ba2;
      font-size: 1.3em;
      margin: 20px 0 15px 0;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin: 20px 0;
    }
    .card {
      background: #f9f9f9;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 20px;
      transition: all 0.3s ease;
    }
    .card:hover {
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
      transform: translateY(-2px);
    }
    .card h4 {
      color: #667eea;
      margin-bottom: 15px;
      font-size: 1.1em;
    }
    .stat-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid #e0e0e0;
    }
    .stat-row:last-child {
      border-bottom: none;
    }
    .stat-label {
      color: #666;
      font-size: 0.95em;
    }
    .stat-value {
      font-weight: 700;
      color: #764ba2;
      font-size: 1.1em;
    }
    .revenue-highlight {
      background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
      border-left: 4px solid #667eea;
      padding: 20px;
      border-radius: 4px;
      margin: 20px 0;
    }
    .revenue-highlight strong {
      color: #667eea;
      font-size: 1.3em;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
    }
    th {
      background: #f0f0f0;
      padding: 12px;
      text-align: left;
      font-weight: 700;
      color: #667eea;
      border-bottom: 2px solid #667eea;
    }
    td {
      padding: 12px;
      border-bottom: 1px solid #e0e0e0;
    }
    tr:hover {
      background: #f9f9f9;
    }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.85em;
      font-weight: 600;
    }
    .badge.high {
      background: #d4edda;
      color: #155724;
    }
    .badge.medium {
      background: #fff3cd;
      color: #856404;
    }
    .badge.low {
      background: #f8d7da;
      color: #721c24;
    }
    .pod-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin: 20px 0;
    }
    .pod-card {
      background: linear-gradient(135deg, #667eea05 0%, #764ba205 100%);
      border: 1px solid #667eea30;
      border-radius: 8px;
      padding: 20px;
    }
    .pod-card h4 {
      color: #667eea;
      margin-bottom: 10px;
      font-size: 1.2em;
      text-transform: capitalize;
    }
    .pod-concept {
      color: #666;
      font-style: italic;
      margin: 10px 0;
      font-size: 0.95em;
    }
    .pod-stats {
      background: white;
      padding: 15px;
      border-radius: 4px;
      margin-top: 15px;
      font-size: 0.9em;
    }
    .pod-stat {
      display: flex;
      justify-content: space-between;
      padding: 5px 0;
    }
    .scenario-box {
      background: white;
      border: 2px solid #667eea;
      border-radius: 8px;
      padding: 20px;
      margin: 15px 0;
    }
    .scenario-box.conservative {
      border-color: #f8d7da;
    }
    .scenario-box.baseline {
      border-color: #667eea;
    }
    .scenario-box.optimistic {
      border-color: #d4edda;
    }
    .scenario-title {
      font-weight: 700;
      margin-bottom: 10px;
      font-size: 1.1em;
    }
    .scenario-desc {
      color: #666;
      font-size: 0.9em;
      margin-bottom: 10px;
    }
    .checklist {
      list-style: none;
      padding: 0;
    }
    .checklist li {
      padding: 10px;
      padding-left: 30px;
      position: relative;
      background: white;
      margin: 5px 0;
      border-radius: 4px;
    }
    .checklist li:before {
      content: "✓";
      position: absolute;
      left: 10px;
      color: #667eea;
      font-weight: bold;
    }
    footer {
      background: #f9f9f9;
      padding: 20px 40px;
      text-align: center;
      border-top: 1px solid #e0e0e0;
      color: #666;
      font-size: 0.9em;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Monetization Report</h1>
      <p>${report.articleMetadata.title}</p>
      <p style="font-size: 0.95em; margin-top: 10px;">Generated: ${report.reportDate}</p>
    </header>

    <div class="content">
      <!-- Article Metadata -->
      <section class="section">
        <h2>Article Metrics</h2>
        <div class="grid">
          <div class="card">
            <h4>Content Length</h4>
            <div class="stat-row">
              <span class="stat-label">Word Count</span>
              <span class="stat-value">${report.articleMetadata.wordCount}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Estimated Pages</span>
              <span class="stat-value">${report.articleMetadata.estimatedPages}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Reading Time</span>
              <span class="stat-value">${report.articleMetadata.readingTimeMinutes} min</span>
            </div>
          </div>
          <div class="card">
            <h4>Content Type</h4>
            <div class="stat-row">
              <span class="stat-label">Topic</span>
              <span class="stat-value">${report.articleMetadata.topic}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Recommendation</span>
              <span class="stat-value">${report.articleMetadata.contentRecommendation}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Gumroad Ebook Product -->
      <section class="section">
        <h2>Gumroad Ebook Product</h2>
        <div class="grid">
          <div class="card">
            <h4>${report.gumroadEbook.productName}</h4>
            <div class="stat-row">
              <span class="stat-label">Product Price</span>
              <span class="stat-value">$${report.gumroadEbook.suggestedPrice.toFixed(2)}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Est. Monthly Units</span>
              <span class="stat-value">${report.gumroadEbook.estimatedMonthlyUnits}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Monthly Revenue</span>
              <span class="stat-value" style="color: #667eea;">$${report.gumroadEbook.estimatedMonthlyRevenue.toFixed(2)}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Yearly Revenue</span>
              <span class="stat-value" style="color: #667eea; font-size: 1.2em;">$${report.gumroadEbook.yearlyProjection.toFixed(2)}</span>
            </div>
          </div>
          <div class="card">
            <h4>Features & Description</h4>
            <p style="color: #666; margin: 10px 0; line-height: 1.5;">${report.gumroadEbook.description}</p>
            <h5 style="color: #764ba2; margin-top: 15px; font-size: 0.95em;">Included:</h5>
            <ul style="margin-left: 20px; color: #666; font-size: 0.9em;">
              ${report.gumroadEbook.tier1Features.map(f => `<li>${f}</li>`).join('')}
            </ul>
          </div>
        </div>
      </section>

      <!-- POD Products -->
      <section class="section">
        <h2>Printify Print-On-Demand Products (${report.printifyPODProducts.length} items)</h2>
        <div class="pod-grid">
          ${report.printifyPODProducts.map(product => `
            <div class="pod-card">
              <h4>${product.productType}</h4>
              <p class="pod-concept">${product.concept}</p>
              <div class="pod-stats">
                <div class="pod-stat">
                  <span>Production Cost:</span>
                  <strong>$${product.estimatedCost.toFixed(2)}</strong>
                </div>
                <div class="pod-stat">
                  <span>Retail Price:</span>
                  <strong>$${product.retailPrice.toFixed(2)}</strong>
                </div>
                <div class="pod-stat">
                  <span>Profit/Unit:</span>
                  <strong style="color: #667eea;">$${product.profitPerUnit.toFixed(2)}</strong>
                </div>
                <div class="pod-stat">
                  <span>Est. Monthly Volume:</span>
                  <strong>${product.estimatedMonthlyVolume}</strong>
                </div>
                <div class="pod-stat" style="border-top: 1px solid #e0e0e0; padding-top: 8px; margin-top: 8px;">
                  <span>Monthly Profit:</span>
                  <strong style="color: #667eea; font-size: 1.1em;">$${product.estimatedMonthlyProfit.toFixed(2)}</strong>
                </div>
              </div>
              <p style="font-size: 0.85em; color: #999; margin-top: 10px;">Target: ${product.targetAudience}</p>
            </div>
          `).join('')}
        </div>
      </section>

      <!-- Revenue Projections -->
      <section class="section">
        <h2>Revenue Projections</h2>

        <h3>Single Article Potential</h3>
        <div class="revenue-highlight">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
            <div>
              <div style="color: #666; margin-bottom: 5px;">Monthly Revenue</div>
              <div><strong>$${report.combinedProjections.singleArticleMonthly.toFixed(2)}</strong></div>
            </div>
            <div>
              <div style="color: #666; margin-bottom: 5px;">Annual Revenue</div>
              <div><strong>$${report.combinedProjections.singleArticleYearly.toFixed(2)}</strong></div>
            </div>
          </div>
        </div>

        <h3 style="margin-top: 30px;">Portfolio Scenarios</h3>
        <table>
          <thead>
            <tr>
              <th>Portfolio Size</th>
              <th>Monthly Revenue</th>
              <th>Annual Revenue</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>50 Articles</strong></td>
              <td style="color: #667eea; font-weight: 600;">$${report.combinedProjections.portfolio50ArticlesMonthly.toFixed(2)}</td>
              <td style="color: #667eea; font-weight: 600;">$${report.combinedProjections.portfolio50ArticlesYearly.toFixed(2)}</td>
            </tr>
            <tr>
              <td><strong>100 Articles</strong></td>
              <td style="color: #667eea; font-weight: 600;">$${report.combinedProjections.portfolio100ArticlesMonthly.toFixed(2)}</td>
              <td style="color: #667eea; font-weight: 600;">$${report.combinedProjections.portfolio100ArticlesYearly.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>

        <h3 style="margin-top: 30px;">Conversion Scenarios (Single Article)</h3>
        <div class="scenario-box conservative">
          <div class="scenario-title">Conservative Estimate (50% conversion)</div>
          <div class="scenario-desc">${report.summaryScenarios.conservativeEstimate.description}</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
            <div>
              <span style="color: #666;">Monthly:</span>
              <strong style="font-size: 1.2em;">$${report.summaryScenarios.conservativeEstimate.monthlyRevenue.toFixed(2)}</strong>
            </div>
            <div>
              <span style="color: #666;">Yearly:</span>
              <strong style="font-size: 1.2em;">$${report.summaryScenarios.conservativeEstimate.yearlyRevenue.toFixed(2)}</strong>
            </div>
          </div>
        </div>

        <div class="scenario-box baseline">
          <div class="scenario-title">Baseline Estimate (100% conversion)</div>
          <div class="scenario-desc">${report.summaryScenarios.baselineEstimate.description}</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
            <div>
              <span style="color: #666;">Monthly:</span>
              <strong style="font-size: 1.2em;">$${report.summaryScenarios.baselineEstimate.monthlyRevenue.toFixed(2)}</strong>
            </div>
            <div>
              <span style="color: #666;">Yearly:</span>
              <strong style="font-size: 1.2em;">$${report.summaryScenarios.baselineEstimate.yearlyRevenue.toFixed(2)}</strong>
            </div>
          </div>
        </div>

        <div class="scenario-box optimistic">
          <div class="scenario-title">Optimistic Estimate (150% conversion)</div>
          <div class="scenario-desc">${report.summaryScenarios.optimisticEstimate.description}</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
            <div>
              <span style="color: #666;">Monthly:</span>
              <strong style="font-size: 1.2em;">$${report.summaryScenarios.optimisticEstimate.monthlyRevenue.toFixed(2)}</strong>
            </div>
            <div>
              <span style="color: #666;">Yearly:</span>
              <strong style="font-size: 1.2em;">$${report.summaryScenarios.optimisticEstimate.yearlyRevenue.toFixed(2)}</strong>
            </div>
          </div>
        </div>
      </section>

      <!-- Implementation Roadmap -->
      <section class="section">
        <h2>Implementation Roadmap</h2>
        <ol class="checklist">
          ${report.nextSteps.map(step => `<li>${step}</li>`).join('')}
        </ol>
      </section>

      <!-- Key Insights -->
      <section class="section">
        <h2>Key Insights</h2>
        <div class="grid">
          <div class="card">
            <h4>Channel Mix</h4>
            <p style="color: #666; font-size: 0.9em; margin: 10px 0;">
              This article generates revenue through two complementary channels:
            </p>
            <ul style="margin-left: 20px; color: #666; font-size: 0.9em; line-height: 1.6;">
              <li><strong>Ebook (Gumroad):</strong> One-time purchase, high margin</li>
              <li><strong>POD (Printify):</strong> Recurring sales, passive fulfillment</li>
            </ul>
          </div>
          <div class="card">
            <h4>Scaling Strategy</h4>
            <p style="color: #666; font-size: 0.9em; margin: 10px 0;">
              Revenue compounds with each new article. With consistent publishing:
            </p>
            <ul style="margin-left: 20px; color: #666; font-size: 0.9em; line-height: 1.6;">
              <li>1 article/week = 50 articles in 1 year</li>
              <li>$${(report.combinedProjections.portfolio50ArticlesMonthly * 12).toFixed(0)}/year potential</li>
            </ul>
          </div>
          <div class="card">
            <h4>Next Focus</h4>
            <p style="color: #666; font-size: 0.9em; margin: 10px 0;">
              Immediate action items to maximize revenue:
            </p>
            <ul style="margin-left: 20px; color: #666; font-size: 0.9em; line-height: 1.6;">
              <li>Create ebook PDF</li>
              <li>Launch Gumroad product</li>
              <li>Design first POD mockups</li>
            </ul>
          </div>
        </div>
      </section>
    </div>

    <footer>
      <p>Generated by ProfitEngine v5 Monetization System</p>
      <p style="margin-top: 10px; font-size: 0.85em;">This report is based on conservative estimates. Actual results may vary.</p>
    </footer>
  </div>
</body>
</html>`;
}

// Main execution
async function main() {
  const args = parseArgs();

  // Use sample article if no file provided
  let article = {
    title: 'Small Steps Build Financial Momentum',
    topic: 'Finance',
    content: `Saving and investing can feel intimidating when the starting point is small. The practical answer is not to wait until everything is perfect. The practical answer is to build the habit, keep the process simple, and let consistency do part of the work.

Acorns is one option that can help people begin with small, repeatable actions. It is not a guaranteed outcome and it is not a substitute for a personal financial plan, but it can be a useful starting point for people who need a simple way to begin.

## Why Small Starts Matter

Small starts reduce friction. A simple first step helps create momentum. Once the habit exists, it becomes easier to improve the system, increase consistency, and make better decisions over time.

## Referral Offer

Eligible new users who join through this referral link can receive a free \$5 investment:

https://acorns.com/share/?shareable_code=NTFH6FL&first_name=Stephen&friend_reward=5

As part of the referral program, I may receive a referral reward too.

## Operating Principle

Start small. Stay consistent. Let the habit compound.

Disclosure: Referral rewards and eligibility are subject to provider terms.`
  };

  if (args.articlePath) {
    const loaded = loadArticle(args.articlePath);
    if (loaded) article = loaded;
  }

  console.log('\n=== Monetization Report Generator ===\n');
  console.log(`Article: "${article.title}"`);
  console.log('Running monetization test...\n');

  try {
    const result = await monetization.runMonetizationTest(article);

    if (!result.success) {
      console.error(`Test failed: ${result.error}`);
      process.exit(1);
    }

    // Generate HTML report
    const htmlReport = generateHTMLReport(result);

    // Determine output path
    const outputPath = args.outputPath || `monetization_report_${Date.now()}.html`;

    // Write HTML report
    fs.writeFileSync(outputPath, htmlReport);
    console.log(`✓ HTML report generated: ${outputPath}`);

    // Write JSON report
    const jsonPath = outputPath.replace('.html', '.json');
    fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
    console.log(`✓ JSON report generated: ${jsonPath}`);

    // Print summary to console
    const report = result.report;
    console.log('\n=== SUMMARY ===\n');
    console.log(`Article: "${report.articleMetadata.title}"`);
    console.log(`Word Count: ${report.articleMetadata.wordCount} words`);
    console.log(`Ebook: ${report.gumroadEbook.productName}`);
    console.log(`Price: $${report.gumroadEbook.suggestedPrice}`);
    console.log(`POD Products: ${report.printifyPODProducts.length}`);
    console.log(`\nRevenue Potential:`);
    console.log(`  Single Article: $${report.combinedProjections.singleArticleMonthly.toFixed(2)}/month`);
    console.log(`  50 Articles: $${report.combinedProjections.portfolio50ArticlesMonthly.toFixed(2)}/month`);
    console.log(`  100 Articles: $${report.combinedProjections.portfolio100ArticlesMonthly.toFixed(2)}/month`);
    console.log();

  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

main();
