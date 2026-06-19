'use strict';
/**
 * app/api/monetization/test/route.js
 * Endpoint to run end-to-end monetization test: article → ebook + POD report
 */

const monetization = require('../../../../agents/monetization');

export async function POST(request) {
  try {
    const { article } = await request.json();

    if (!article || !article.title) {
      return Response.json(
        { success: false, error: 'Invalid article structure' },
        { status: 400 }
      );
    }

    // Prepare article object with content
    const articleData = {
      title: article.title || 'Untitled',
      topic: article.topic || 'General',
      content: article.content || article.body || '',
      wordCount: (article.content || article.body || '').split(/\s+/).length
    };

    // Run monetization test
    const result = await monetization.runMonetizationTest(articleData);

    return Response.json(result, { status: 200 });
  } catch (error) {
    console.error('Monetization test error:', error);
    return Response.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
