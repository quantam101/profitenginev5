#!/usr/bin/env node
/**
 * tests/run_monetization_tests.js
 * Execute full Gumroad + Printify monetization E2E tests
 * Shows real numbers and generates monetization dashboard
 */

const fs = require('fs');
const path = require('path');

// Mock articles from generated content
const testArticles = [
  {
    title: 'Small Steps Build Financial Momentum',
    topic: 'Finance',
    content: fs.readFileSync(
      path.join(__dirname, '../generated-content/acorns-referral-2026-06-09/blog/article.md'),
      'utf8'
    )
  }
];

// Simple test runner
async function runTests() {
  const monetization = require('../agents/monetization');

  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║    GUMROAD + PRINTIFY MONETIZATION SYSTEM E2E TEST            ║');
  console.log('║           Article → Ebook + POD Products                      ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const allResults = [];

  for (const article of testArticles) {
    console.log(`\n📄 Testing Article: "${article.title}"\n`);

    try {
      // Step 1: Analyze article
      console.log('Step 1: Analyzing article for ebook conversion...');
      const ebookMetadata = monetization.analyzeArticleForEbook(article);

      if (!ebookMetadata) {
        console.error('✗ Article analysis failed');
        continue;
      }

      console.log(`  ✓ Word count: ${ebookMetadata.wordCount}`);
      console.log(`  ✓ Reading time: ${ebookMetadata.readingTimeMinutes} minutes`);
      console.log(`  ✓ Estimated pages: ${ebookMetadata.ebookReadiness.estimatedPages}`);
      console.log(`  ✓ Recommendation: ${ebookMetadata.ebookReadiness.recommendation}\n`);

      // Step 2: Generate Gumroad product
      console.log('Step 2: Generating Gumroad ebook product...');
      const gumroadProduct = await monetization.generateGumroadProduct(article, ebookMetadata);

      if (!gumroadProduct) {
        console.error('✗ Gumroad product generation failed');
        continue;
      }

      console.log(`  ✓ Product name: ${gumroadProduct.productName}`);
      console.log(`  ✓ Suggested price: $${gumroadProduct.suggestedPrice.toFixed(2)}`);
      console.log(`  ✓ Est. monthly units: ${gumroadProduct.estimatedMonthlyUnits}`);
      console.log(`  ✓ Est. monthly revenue: $${gumroadProduct.estimatedMonthlyRevenue.toFixed(2)}`);
      console.log(`  ✓ Est. yearly revenue: $${(gumroadProduct.estimatedMonthlyRevenue * 12).toFixed(2)}\n`);

      // Step 3: Generate POD product ideas
      console.log('Step 3: Generating POD product ideas...');
      const podProducts = await monetization.generatePODProductIdeas(article);

      if (podProducts.length > 0) {
        console.log(`  ✓ Generated ${podProducts.length} POD product concepts\n`);

        podProducts.forEach((product, idx) => {
          console.log(`  Product ${idx + 1}: ${product.productType}`);
          console.log(`    - Concept: ${product.concept}`);
          console.log(`    - Retail price: $${product.suggestedRetailPrice.toFixed(2)}`);
          console.log(`    - Profit per unit: $${product.profitPerUnit.toFixed(2)}`);
          console.log(`    - Est. monthly volume: ${product.estimatedMonthlyVolume} units`);
          console.log(`    - Est. monthly profit: $${product.estimatedMonthlyProfit.toFixed(2)}`);
        });
      } else {
        console.log('  ⚠ No POD products generated (API may not be available)');
      }
      console.log();

      // Step 4: Publish to Gumroad
      console.log('Step 4: Publishing to Gumroad (staging)...');
      const gumroadPublished = await monetization.publishToGumroad(gumroadProduct);

      console.log(`  ✓ Product published (status: ${gumroadPublished.status})`);
      console.log(`  ✓ Product URL: ${gumroadPublished.productUrl || gumroadPublished.url}\n`);

      // Step 5: Generate mockups
      console.log('Step 5: Generating Printify mockups...');
      const mockups = await monetization.generatePrintifyMockups(podProducts);

      if (mockups.length > 0) {
        console.log(`  ✓ Generated ${mockups.length} product mockups\n`);
      } else {
        console.log('  ⚠ No mockups generated\n');
      }

      // Step 6: Generate report
      console.log('Step 6: Generating monetization report...');
      const report = await monetization.generateMonetizationReport(
        article,
        ebookMetadata,
        gumroadProduct,
        podProducts
      );

      console.log(`  ✓ Report generated successfully\n`);

      // Display revenue projections
      console.log('╔════════════════════════════════════════════════════════════════╗');
      console.log('║                    REVENUE PROJECTIONS                         ║');
      console.log('╚════════════════════════════════════════════════════════════════╝\n');

      const single = report.combinedProjections.singleArticleMonthly;
      const portfolio50 = report.combinedProjections.portfolio50ArticlesMonthly;
      const portfolio100 = report.combinedProjections.portfolio100ArticlesMonthly;

      console.log('Single Article:');
      console.log(`  Monthly revenue:    $${single.toFixed(2)}`);
      console.log(`  Yearly revenue:     $${(single * 12).toFixed(2)}\n`);

      console.log('Portfolio of 50 Articles:');
      console.log(`  Monthly revenue:    $${portfolio50.toFixed(2)}`);
      console.log(`  Yearly revenue:     $${(portfolio50 * 12).toFixed(2)}\n`);

      console.log('Portfolio of 100 Articles:');
      console.log(`  Monthly revenue:    $${portfolio100.toFixed(2)}`);
      console.log(`  Yearly revenue:     $${(portfolio100 * 12).toFixed(2)}\n`);

      // Conversion scenarios
      console.log('╔════════════════════════════════════════════════════════════════╗');
      console.log('║                  CONVERSION SCENARIOS                          ║');
      console.log('╚════════════════════════════════════════════════════════════════╝\n');

      const scenarios = report.summaryScenarios;

      console.log('Conservative (50% conversion):');
      console.log(`  Monthly:  $${scenarios.conservativeEstimate.monthlyRevenue.toFixed(2)}`);
      console.log(`  Yearly:   $${scenarios.conservativeEstimate.yearlyRevenue.toFixed(2)}\n`);

      console.log('Baseline (100% conversion):');
      console.log(`  Monthly:  $${scenarios.baselineEstimate.monthlyRevenue.toFixed(2)}`);
      console.log(`  Yearly:   $${scenarios.baselineEstimate.yearlyRevenue.toFixed(2)}\n`);

      console.log('Optimistic (150% conversion):');
      console.log(`  Monthly:  $${scenarios.optimisticEstimate.monthlyRevenue.toFixed(2)}`);
      console.log(`  Yearly:   $${scenarios.optimisticEstimate.yearlyRevenue.toFixed(2)}\n`);

      // Channel breakdown
      console.log('╔════════════════════════════════════════════════════════════════╗');
      console.log('║                    REVENUE BY CHANNEL                          ║');
      console.log('╚════════════════════════════════════════════════════════════════╝\n');

      const ebookMonthly = report.gumroadEbook.estimatedMonthlyRevenue;
      const podMonthly = single - ebookMonthly;

      console.log('Gumroad Ebook:');
      console.log(`  Monthly:  $${ebookMonthly.toFixed(2)} (${(ebookMonthly / single * 100).toFixed(1)}%)`);
      console.log(`  Yearly:   $${(ebookMonthly * 12).toFixed(2)}\n`);

      console.log('Printify POD (3 products):');
      console.log(`  Monthly:  $${podMonthly.toFixed(2)} (${(podMonthly / single * 100).toFixed(1)}%)`);
      console.log(`  Yearly:   $${(podMonthly * 12).toFixed(2)}\n`);

      // Implementation roadmap
      console.log('╔════════════════════════════════════════════════════════════════╗');
      console.log('║                  IMPLEMENTATION ROADMAP                        ║');
      console.log('╚════════════════════════════════════════════════════════════════╝\n');

      report.nextSteps.forEach((step, idx) => {
        console.log(`${idx + 1}. ${step}`);
      });
      console.log();

      allResults.push({
        article: article.title,
        result: {
          success: true,
          report,
          gumroadProduct,
          podProducts
        }
      });

    } catch (err) {
      console.error(`✗ Test failed: ${err.message}`);
      allResults.push({
        article: article.title,
        result: { success: false, error: err.message }
      });
    }
  }

  // Summary statistics
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║                      TEST SUMMARY                              ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const successCount = allResults.filter(r => r.result.success).length;
  const totalCount = allResults.length;

  console.log(`Tests completed: ${successCount}/${totalCount}`);

  if (successCount > 0) {
    const firstSuccess = allResults.find(r => r.result.success)?.result;
    if (firstSuccess) {
      const report = firstSuccess.report;
      console.log(`\nAggregate Potential (100 articles):`);
      console.log(`  Monthly: $${report.combinedProjections.portfolio100ArticlesMonthly.toFixed(2)}`);
      console.log(`  Yearly:  $${report.combinedProjections.portfolio100ArticlesYearly.toFixed(2)}`);
    }
  }

  console.log('\n✓ Monetization E2E tests completed\n');

  // Save results
  const resultsFile = `monetization_test_results_${Date.now()}.json`;
  fs.writeFileSync(resultsFile, JSON.stringify(allResults, null, 2));
  console.log(`Results saved to: ${resultsFile}\n`);
}

// Run tests
runTests().catch(err => {
  console.error(`Fatal error: ${err.message}`);
  process.exit(1);
});
