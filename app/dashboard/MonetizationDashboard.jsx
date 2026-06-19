'use strict';
/**
 * app/dashboard/MonetizationDashboard.jsx
 * Real-time monetization dashboard: articles → ebooks + POD revenue opportunities
 */

import React, { useState, useEffect } from 'react';
import styles from './dashboard.module.css';

export default function MonetizationDashboard() {
  const [articles, setArticles] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadArticles();
  }, []);

  async function loadArticles() {
    try {
      setLoading(true);
      const res = await fetch('/api/content/articles');
      const data = await res.json();
      setArticles(data.articles || []);

      // Generate monetization analysis
      const analyzed = data.articles.map(article => ({
        ...article,
        wordCount: (article.content || '').split(/\s+/).length,
        ebookPotential: (article.content || '').split(/\s+/).length >= 1000 ? 'High' : 'Medium',
        podPotential: categorizeTopicForPOD(article.topic),
        estimatedEbookValue: estimateEbookPrice((article.content || '').split(/\s+/).length),
        estimatedPODValue: estimatePODRevenue(article.topic)
      }));

      setArticles(analyzed);

      // Sort by revenue potential
      const ranked = analyzed.sort((a, b) =>
        (b.estimatedEbookValue + b.estimatedPODValue) -
        (a.estimatedEbookValue + a.estimatedPODValue)
      );
      setOpportunities(ranked);
    } catch (err) {
      console.error('Failed to load articles:', err);
    } finally {
      setLoading(false);
    }
  }

  function categorizeTopicForPOD(topic) {
    const high = ['finance', 'wealth', 'business', 'investing', 'trading', 'marketing'];
    const medium = ['tech', 'lifestyle', 'health', 'education'];

    const topicLower = (topic || '').toLowerCase();
    if (high.some(t => topicLower.includes(t))) return 'High';
    if (medium.some(t => topicLower.includes(t))) return 'Medium';
    return 'Low';
  }

  function estimateEbookPrice(wordCount) {
    // $5-$9.99 per ebook based on word count
    if (wordCount < 1000) return 4.99;
    if (wordCount < 5000) return 7.99;
    if (wordCount < 10000) return 12.99;
    return 19.99;
  }

  function estimatePODRevenue(topic) {
    // Estimate monthly revenue from 3 POD products
    // Based on niche relevance
    const baseMonthly = 50; // $50-$150 per product per month

    const topicLower = (topic || '').toLowerCase();
    if (topicLower.includes('finance') || topicLower.includes('wealth')) return baseMonthly * 3 * 2;
    if (topicLower.includes('business') || topicLower.includes('investing')) return baseMonthly * 3 * 1.5;
    return baseMonthly * 3;
  }

  async function runMonetizationTest(article) {
    setLoading(true);
    try {
      const res = await fetch('/api/monetization/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article })
      });
      const result = await res.json();
      setReport(result);
      setSelectedArticle(article);
    } catch (err) {
      console.error('Test failed:', err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.dashboardContainer}>
      <header className={styles.dashboardHeader}>
        <h1>Content Monetization Dashboard</h1>
        <p>Articles → Ebooks (Gumroad) + POD Products (Printify)</p>
      </header>

      <div className={styles.gridContainer}>
        {/* Left Panel: Article Analysis */}
        <section className={styles.panel}>
          <h2>Articles Analyzed</h2>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <span className={styles.label}>Total Articles</span>
              <span className={styles.value}>{articles.length}</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.label}>Ebook Ready (&gt;1000w)</span>
              <span className={styles.value}>{articles.filter(a => a.wordCount > 1000).length}</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.label}>POD Potential</span>
              <span className={styles.value}>{articles.filter(a => a.podPotential === 'High').length}</span>
            </div>
          </div>

          <div className={styles.articleList}>
            {articles.map((article, idx) => (
              <div key={idx} className={styles.articleCard}>
                <h3>{article.title || `Article ${idx + 1}`}</h3>
                <div className={styles.meta}>
                  <span className={styles.wordCount}>{article.wordCount} words</span>
                  <span className={`${styles.badge} ${styles[article.ebookPotential.toLowerCase()]}`}>
                    {article.ebookPotential} Ebook
                  </span>
                  <span className={`${styles.badge} ${styles[article.podPotential.toLowerCase()]}`}>
                    {article.podPotential} POD
                  </span>
                </div>
                <div className={styles.potential}>
                  <div className={styles.potentialRow}>
                    <span>Ebook potential:</span>
                    <strong>${article.estimatedEbookValue.toFixed(2)}</strong>
                  </div>
                  <div className={styles.potentialRow}>
                    <span>POD monthly:</span>
                    <strong>${article.estimatedPODValue.toFixed(2)}</strong>
                  </div>
                  <div className={styles.potentialRow}>
                    <span>Combined/month:</span>
                    <strong className={styles.highlight}>
                      ${(article.estimatedEbookValue + article.estimatedPODValue).toFixed(2)}
                    </strong>
                  </div>
                </div>
                <button
                  className={styles.button}
                  onClick={() => runMonetizationTest(article)}
                  disabled={loading}
                >
                  {loading && selectedArticle === article ? 'Testing...' : 'Test Monetization'}
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Center Panel: Revenue Opportunities */}
        <section className={styles.panel}>
          <h2>Revenue Opportunities (Ranked)</h2>

          <div className={styles.projections}>
            <div className={styles.projectionBox}>
              <h3>Single Article Potential</h3>
              {selectedArticle && report ? (
                <>
                  <div className={styles.projectionRow}>
                    <span>Monthly Revenue</span>
                    <strong>${report.report?.combinedProjections?.singleArticleMonthly.toFixed(2) || '0.00'}</strong>
                  </div>
                  <div className={styles.projectionRow}>
                    <span>Yearly Revenue</span>
                    <strong className={styles.highlight}>
                      ${(report.report?.combinedProjections?.singleArticleMonthly * 12).toFixed(2) || '0.00'}
                    </strong>
                  </div>
                </>
              ) : (
                <p className={styles.placeholder}>Select an article to see projections</p>
              )}
            </div>

            <div className={styles.projectionBox}>
              <h3>Portfolio Growth (50 Articles)</h3>
              {report ? (
                <>
                  <div className={styles.projectionRow}>
                    <span>Monthly Revenue</span>
                    <strong>${report.report?.combinedProjections?.portfolio50ArticlesMonthly.toFixed(2) || '0.00'}</strong>
                  </div>
                  <div className={styles.projectionRow}>
                    <span>Yearly Revenue</span>
                    <strong className={styles.highlight}>
                      ${report.report?.combinedProjections?.portfolio50ArticlesYearly.toFixed(2) || '0.00'}
                    </strong>
                  </div>
                </>
              ) : (
                <p className={styles.placeholder}>$2,500 - $5,000/month potential</p>
              )}
            </div>

            <div className={styles.projectionBox}>
              <h3>Full Portfolio (100 Articles)</h3>
              {report ? (
                <>
                  <div className={styles.projectionRow}>
                    <span>Monthly Revenue</span>
                    <strong>${report.report?.combinedProjections?.portfolio100ArticlesMonthly.toFixed(2) || '0.00'}</strong>
                  </div>
                  <div className={styles.projectionRow}>
                    <span>Yearly Revenue</span>
                    <strong className={styles.highlight}>
                      ${report.report?.combinedProjections?.portfolio100ArticlesYearly.toFixed(2) || '0.00'}
                    </strong>
                  </div>
                </>
              ) : (
                <p className={styles.placeholder}>$5,000 - $15,000/month potential</p>
              )}
            </div>
          </div>

          <div className={styles.opportunityList}>
            <h3>Top Opportunities</h3>
            {opportunities.slice(0, 5).map((opp, idx) => (
              <div key={idx} className={styles.opportunity}>
                <div className={styles.rank}>#{idx + 1}</div>
                <div className={styles.oppContent}>
                  <h4>{opp.title || `Article ${idx + 1}`}</h4>
                  <p>{opp.topic}</p>
                </div>
                <div className={styles.oppValue}>
                  ${(opp.estimatedEbookValue + opp.estimatedPODValue).toFixed(2)}/mo
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Right Panel: Test Results & Products */}
        <section className={styles.panel}>
          <h2>Monetization Report</h2>

          {report ? (
            <>
              <div className={styles.reportSection}>
                <h3>Ebook Product</h3>
                <div className={styles.reportContent}>
                  <p><strong>Name:</strong> {report.gumroadProduct?.productName}</p>
                  <p><strong>Price:</strong> ${report.gumroadProduct?.suggestedPrice}</p>
                  <p><strong>Estimated Units/Month:</strong> {report.gumroadProduct?.estimatedMonthlyUnits}</p>
                  <p><strong>Monthly Revenue:</strong> ${report.gumroadProduct?.estimatedMonthlyRevenue}</p>
                  <p><strong>Yearly Revenue:</strong> ${(report.gumroadProduct?.estimatedMonthlyRevenue * 12).toFixed(2)}</p>
                </div>
              </div>

              <div className={styles.reportSection}>
                <h3>POD Products ({report.podProductIdeas?.length})</h3>
                <div className={styles.podProducts}>
                  {report.podProductIdeas?.map((product, idx) => (
                    <div key={idx} className={styles.podProduct}>
                      <h4>{product.productType}</h4>
                      <p className={styles.concept}>{product.concept}</p>
                      <div className={styles.podStats}>
                        <div>Cost: ${product.estimatedCost.toFixed(2)}</div>
                        <div>Price: ${product.suggestedRetailPrice.toFixed(2)}</div>
                        <div>Profit/unit: ${product.profitPerUnit.toFixed(2)}</div>
                        <div className={styles.monthly}>Monthly: ${product.estimatedMonthlyProfit.toFixed(2)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.reportSection}>
                <h3>Next Steps</h3>
                <ol className={styles.nextSteps}>
                  {report.report?.nextSteps?.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
              </div>
            </>
          ) : (
            <p className={styles.placeholder}>Select an article and click "Test Monetization" to generate a report</p>
          )}
        </section>
      </div>
    </div>
  );
}
