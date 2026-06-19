'use strict';

export async function POST(request) {
  try {
    const { article } = await request.json();

    if (!article || !article.title) {
      return Response.json(
        { success: false, error: 'Invalid article structure' },
        { status: 400 }
      );
    }

    const content = article.content || article.body || '';
    const articleData = {
      title: article.title || 'Untitled',
      topic: article.topic || 'General',
      content,
      wordCount: content.trim() ? content.trim().split(/\s+/).length : 0
    };

    const agent = await import('../../../../agents/monetization.mjs');
    const result = await agent.runMonetizationTest(articleData);

    return Response.json(result, { status: 200 });
  } catch (error) {
    console.error('Monetization test error:', error);
    return Response.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
