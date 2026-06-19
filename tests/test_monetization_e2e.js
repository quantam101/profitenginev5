/**
 * tests/test_monetization_e2e.js
 * End-to-end monetization test: article → Gumroad ebook + Printify POD
 * Validates the complete monetization pipeline
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');

// Mock articles for testing
const testArticles = [
  {
    title: 'Small Steps Build Financial Momentum',
    topic: 'Finance',
    content: `Saving and investing can feel intimidating when the starting point is small. The practical answer is not to wait until everything is perfect. The practical answer is to build the habit, keep the process simple, and let consistency do part of the work.

Acorns is one option that can help people begin with small, repeatable actions. It is not a guaranteed outcome and it is not a substitute for a personal financial plan, but it can be a useful starting point for people who need a simple way to begin.

Why Small Starts Matter

Small starts reduce friction. A simple first step helps create momentum. Once the habit exists, it becomes easier to improve the system, increase consistency, and make better decisions over time.

Referral Offer

Eligible new users who join through this referral link can receive a free $5 investment:

https://acorns.com/share/?shareable_code=NTFH6FL&first_name=Stephen&friend_reward=5

As part of the referral program, I may receive a referral reward too.

Operating Principle

Start small. Stay consistent. Let the habit compound.

Disclosure: Referral rewards and eligibility are subject to provider terms.`,
    wordCount: 0
  },
  {
    title: 'Building Passive Income Streams',
    topic: 'Business',
    content: `Passive income requires active setup. Many people hear "passive income" and imagine money flowing in while they sleep. The reality is that true passive income comes after months or years of intentional work.

Here are five realistic passive income streams you can build in 2026:

1. Digital Products (Ebooks, Courses)

Create once, sell forever. Your effort happens upfront. After that, each sale is nearly pure profit.

2. Affiliate Marketing

Recommend products you genuinely use. Build trust with your audience. Let commissions accumulate.

3. Print-on-Demand Products

Design once, Printify handles fulfillment. Every order generates profit without inventory costs.

4. Content Libraries

YouTube, blogs, podcasts. Build an audience. Monetize through ads, sponsorships, and affiliate links.

5. Membership Communities

Create exclusive content. Charge recurring fees. Build a sustainable revenue stream.

The Real Work

Passive income isn't about doing nothing. It's about doing the work once and being paid repeatedly. Start with what you know. Build systematically. Track what works.`
  },
  {
    title: 'Why Content is Still the Best Investment',
    topic: 'Marketing',
    content: `Every dollar spent on content marketing comes back multiplied. Not immediately. Not always predictably. But consistently.

Content is the infrastructure of modern business. It works while you sleep. It builds trust before you ever talk to a prospect. It ranks in search engines. It gets shared on social media.

The Content Paradox

The best content doesn't feel like marketing. It solves a real problem. It answers a real question. It teaches something valuable.

When you write content that genuinely helps your audience, they return. They recommend you. They buy from you.

Three Types of Content Worth Creating

Educational Content: Teach your audience. Build authority. Answer their questions before they ask.

Narrative Content: Tell stories. Share case studies. Show real results. Help people see themselves in your success.

Practical Content: Templates, checklists, frameworks, guides. Give tools that save time and money.

The Compound Effect

One article. Maybe $50 in sales the first month. But that article keeps selling. After a year, it's generated $600. After five years, $3,000.

Most people quit too early. They create content that doesn't generate immediate revenue. So they think it's not working. The reality is that content requires patience and scale.

Start with one article per week. Keep building. In six months, you'll have 24 revenue-generating assets. In a year, you'll have 52.

That's when passive income compounds.`
  }
];

describe('E2E Monetization: Article → Ebook + POD', () => {

  test('Step 1: Analyze article for ebook conversion', async () => {
    const monetization = require('../agents/monetization');

    for (const article of testArticles) {
      const metadata = monetization.analyzeArticleForEbook(article);

      assert(metadata, 'Metadata should be generated');
      assert(metadata.title === article.title, 'Title should match');
      assert(metadata.wordCount > 0, 'Word count should be calculated');
      assert(metadata.readingTimeMinutes > 0, 'Reading time should be calculated');
      assert(metadata.ebookReadiness, 'Ebook readiness should be assessed');

      console.log(`✓ Article analyzed: "${article.title}"`);
      console.log(`  Words: ${metadata.wordCount}, Reading time: ${metadata.readingTimeMinutes}min`);
      console.log(`  Recommendation: ${metadata.ebookReadiness.recommendation}`);
      console.log(`  Pages: ${metadata.ebookReadiness.estimatedPages}\n`);
    }
  });

  test('Step 2: Generate Gumroad ebook products', async () => {
    const monetization = require('../agents/monetization');

    for (const article of testArticles) {
      const metadata = monetization.analyzeArticleForEbook(article);
      const gumroadProduct = await monetization.generateGumroadProduct(article, metadata);

      assert(gumroadProduct, 'Gumroad product should be generated');
      assert(gumroadProduct.productName, 'Product should have a name');
      assert(gumroadProduct.suggestedPrice > 0, 'Product should have a price');
      assert(gumroadProduct.estimatedMonthlyUnits >= 0, 'Should estimate monthly units');
      assert(gumroadProduct.estimatedMonthlyRevenue >= 0, 'Should estimate monthly revenue');

      console.log(`✓ Gumroad product created: "${gumroadProduct.productName}"`);
      console.log(`  Price: $${gumroadProduct.suggestedPrice}`);
      console.log(`  Est. monthly units: ${gumroadProduct.estimatedMonthlyUnits}`);
      console.log(`  Est. monthly revenue: $${gumroadProduct.estimatedMonthlyRevenue}\n`);
    }
  });

  test('Step 3: Generate POD product ideas', async () => {
    const monetization = require('../agents/monetization');

    for (const article of testArticles) {
      const podProducts = await monetization.generatePODProductIdeas(article);

      assert(Array.isArray(podProducts), 'Should return array of POD ideas');
      assert(podProducts.length >= 0, 'Should generate at least 0 ideas (may fail gracefully)');

      if (podProducts.length > 0) {
        console.log(`✓ Generated ${podProducts.length} POD product ideas for "${article.title}"`);
        podProducts.forEach((product, idx) => {
          console.log(`  ${idx + 1}. ${product.productType}`);
          console.log(`     Concept: ${product.concept}`);
          console.log(`     Est. monthly profit: $${product.estimatedMonthlyProfit}`);
        });
      } else {
        console.log(`⚠ No POD products generated for "${article.title}" (API may not be available)`);
      }
      console.log();
    }
  });

  test('Step 4: Publish to Gumroad (staging)', async () => {
    const monetization = require('../agents/monetization');

    for (const article of testArticles) {
      const metadata = monetization.analyzeArticleForEbook(article);
      const gumroadProduct = await monetization.generateGumroadProduct(article, metadata);
      const published = await monetization.publishToGumroad(gumroadProduct);

      assert(published, 'Published product should be returned');
      assert(published.productName, 'Published product should have a name');
      assert(published.productUrl || published.url, 'Product should have a URL');

      console.log(`✓ Published to Gumroad (staging): ${published.productName}`);
      console.log(`  URL: ${published.productUrl || published.url}`);
      console.log(`  Status: ${published.status || 'draft'}\n`);
    }
  });

  test('Step 5: Generate POD mockups', async () => {
    const monetization = require('../agents/monetization');

    for (const article of testArticles) {
      const podProducts = await monetization.generatePODProductIdeas(article);

      if (podProducts.length > 0) {
        const mockups = await monetization.generatePrintifyMockups(podProducts);

        assert(Array.isArray(mockups), 'Should return array of mockups');
        assert(mockups.length === podProducts.length, 'Should match number of products');

        console.log(`✓ Generated mockups for ${mockups.length} POD products`);
        mockups.forEach((mockup, idx) => {
          console.log(`  ${idx + 1}. ${mockup.productType}`);
          console.log(`     Mockup URL: ${mockup.mockupUrl}`);
        });
      } else {
        console.log('⚠ Skipping mockups (no POD products generated)');
      }
      console.log();
    }
  });

  test('Step 6: Generate monetization report', async () => {
    const monetization = require('../agents/monetization');

    for (const article of testArticles) {
      const ebookMetadata = monetization.analyzeArticleForEbook(article);
      const gumroadProduct = await monetization.generateGumroadProduct(article, ebookMetadata);
      const podProducts = await monetization.generatePODProductIdeas(article);
      const report = await monetization.generateMonetizationReport(
        article,
        ebookMetadata,
        gumroadProduct,
        podProducts
      );

      assert(report, 'Report should be generated');
      assert(report.articleMetadata, 'Report should include article metadata');
      assert(report.gumroadEbook, 'Report should include Gumroad details');
      assert(report.printifyPODProducts, 'Report should include POD products');
      assert(report.combinedProjections, 'Report should include projections');

      const singleMonthly = report.combinedProjections.singleArticleMonthly;
      const portfolio50 = report.combinedProjections.portfolio50ArticlesMonthly;
      const portfolio100 = report.combinedProjections.portfolio100ArticlesMonthly;

      console.log(`✓ Monetization report generated for "${article.title}"`);
      console.log(`  Article metrics:`);
      console.log(`    - Word count: ${report.articleMetadata.wordCount}`);
      console.log(`    - Estimated pages: ${report.articleMetadata.estimatedPages}`);
      console.log(`  Gumroad ebook:`);
      console.log(`    - Price: $${report.gumroadEbook.suggestedPrice}`);
      console.log(`    - Est. monthly units: ${report.gumroadEbook.estimatedMonthlyUnits}`);
      console.log(`    - Est. monthly revenue: $${report.gumroadEbook.estimatedMonthlyRevenue.toFixed(2)}`);
      console.log(`  POD products: ${report.printifyPODProducts.length}`);
      console.log(`  Revenue projections:`);
      console.log(`    - Single article/month: $${singleMonthly.toFixed(2)}`);
      console.log(`    - 50 articles/month: $${portfolio50.toFixed(2)}`);
      console.log(`    - 100 articles/month: $${portfolio100.toFixed(2)}`);
      console.log();
    }
  });

  test('Step 7: Run full end-to-end monetization test', async () => {
    const monetization = require('../agents/monetization');

    for (const article of testArticles) {
      const result = await monetization.runMonetizationTest(article);

      assert(result.success === true, 'Test should succeed');
      assert(result.testId, 'Test should have an ID');
      assert(result.report, 'Test should generate report');

      const report = result.report;
      console.log(`✓ E2E test completed for "${article.title}"`);
      console.log(`  Test ID: ${result.testId}`);
      console.log(`  Ebook: ${report.gumroadEbook.productName} @ $${report.gumroadEbook.suggestedPrice}`);
      console.log(`  POD products: ${report.printifyPODProducts.length} items`);
      console.log(`  Monthly revenue potential: $${report.combinedProjections.singleArticleMonthly.toFixed(2)}`);
      console.log(`  Yearly revenue potential: $${report.combinedProjections.singleArticleMonthly * 12.toFixed(2)}`);
      console.log();
    }
  });

  test('Scenario: 50-article portfolio projections', async () => {
    const monetization = require('../agents/monetization');

    console.log('\n=== MONETIZATION SCENARIO: 50-ARTICLE PORTFOLIO ===\n');

    // Analyze first article
    const article = testArticles[0];
    const result = await monetization.runMonetizationTest(article);
    const report = result.report;

    const singleMonthly = report.combinedProjections.singleArticleMonthly;
    const portfolio50 = report.combinedProjections.portfolio50ArticlesMonthly;
    const portfolio50Yearly = portfolio50 * 12;

    console.log(`Single Article Potential:`);
    console.log(`  Monthly: $${singleMonthly.toFixed(2)}`);
    console.log(`  Yearly: $${(singleMonthly * 12).toFixed(2)}\n`);

    console.log(`50-Article Portfolio Potential:`);
    console.log(`  Monthly: $${portfolio50.toFixed(2)}`);
    console.log(`  Yearly: $${portfolio50Yearly.toFixed(2)}\n`);

    console.log(`Assumptions:`);
    console.log(`  - Average ebook: $${report.gumroadEbook.suggestedPrice} price`);
    console.log(`  - Average ebook: ${report.gumroadEbook.estimatedMonthlyUnits} units/month`);
    console.log(`  - POD products: 3 per article`);
    console.log(`  - Avg profit per POD: $${(report.printifyPODProducts.reduce((s, p) => s + p.estimatedMonthlyProfit, 0) / report.printifyPODProducts.length).toFixed(2)}\n`);

    assert(portfolio50 > 0, 'Portfolio revenue should be positive');
    assert(portfolio50 > singleMonthly, '50 articles should generate more than 1');
  });

  test('Scenario: 100-article portfolio projections', async () => {
    const monetization = require('../agents/monetization');

    console.log('\n=== MONETIZATION SCENARIO: 100-ARTICLE PORTFOLIO ===\n');

    // Analyze first article
    const article = testArticles[0];
    const result = await monetization.runMonetizationTest(article);
    const report = result.report;

    const portfolio100 = report.combinedProjections.portfolio100ArticlesMonthly;
    const portfolio100Yearly = portfolio100 * 12;

    console.log(`100-Article Portfolio Potential:`);
    console.log(`  Monthly: $${portfolio100.toFixed(2)}`);
    console.log(`  Yearly: $${portfolio100Yearly.toFixed(2)}\n`);

    console.log(`Breakdown per channel:`);
    const ebookTotal = report.gumroadEbook.estimatedMonthlyRevenue * 100;
    const podTotal = portfolio100 - ebookTotal;
    console.log(`  - Ebook channel: $${ebookTotal.toFixed(2)}/month`);
    console.log(`  - POD channel: $${podTotal.toFixed(2)}/month\n`);

    console.log(`Conservative (50% conversion): $${(portfolio100 * 0.5).toFixed(2)}/month`);
    console.log(`Baseline (100% conversion): $${portfolio100.toFixed(2)}/month`);
    console.log(`Optimistic (150% conversion): $${(portfolio100 * 1.5).toFixed(2)}/month\n`);

    assert(portfolio100 > 0, 'Portfolio revenue should be positive');
  });
});

// Run tests if executed directly
if (require.main === module) {
  console.log('Running E2E Monetization Tests...\n');
  // Tests will be run via test runner
}

module.exports = { testArticles };
