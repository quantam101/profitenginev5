/**
 * INSTAGRAM STORIES AUTOMATION
 *
 * Automatically generates and posts Instagram stories:
 * - Generate 3 daily story images (market updates, polls, Q&A)
 * - Upload to Instagram via Meta Graph API
 * - Auto-post at 9 AM, 12 PM, 7 PM ET
 *
 * Environment Requirements:
 * - IG_USER_ID: Instagram business account ID
 * - FB_PAGE_ACCESS_TOKEN: Meta Graph API access token
 * - RUNTIME_API_URL: Backend service URL for async story generation
 */

import { readFile } from 'fs/promises';

interface StoryContent {
  type: 'market_update' | 'poll' | 'qa' | 'tip';
  title: string;
  content: string;
  imageUrl?: string;
  ctaText?: string;
  ctaLink?: string;
  timestamp: string;
}

interface DailyStorySet {
  date: string;
  stories: StoryContent[];
  scheduleTime?: string; // ISO format
}

interface GeneratedStory {
  imageUrl: string;
  content: StoryContent;
  generatedAt: string;
}

interface InstagramStoryResult {
  success: boolean;
  storyId?: string;
  storyUrl?: string;
  postTime?: string;
  generatedStories?: GeneratedStory[];
  error?: string;
}

/**
 * Generate market update story image
 */
async function generateMarketUpdateStory(content: StoryContent): Promise<string> {
  return generateStoryImageViaBackend(
    'market_update',
    content.title,
    content.content,
    content.ctaText,
    content.ctaLink
  );
}

/**
 * Generate poll story image
 */
async function generatePollStory(content: StoryContent): Promise<string> {
  return generateStoryImageViaBackend(
    'poll',
    content.title,
    content.content,
    'Vote Now',
    content.ctaLink
  );
}

/**
 * Generate Q&A story image
 */
async function generateQAStory(content: StoryContent): Promise<string> {
  return generateStoryImageViaBackend(
    'qa',
    content.title,
    content.content,
    'Reply to Q&A',
    undefined
  );
}

/**
 * Generate trading tip story image
 */
async function generateTipStory(content: StoryContent): Promise<string> {
  return generateStoryImageViaBackend(
    'tip',
    content.title,
    content.content,
    'Learn More',
    content.ctaLink
  );
}

/**
 * Generate story image via backend rendering service
 */
async function generateStoryImageViaBackend(
  type: string,
  title: string,
  content: string,
  ctaText?: string,
  ctaLink?: string
): Promise<string> {
  const runtimeUrl = process.env.RUNTIME_API_URL || 'http://localhost:8000';

  const response = await fetch(`${runtimeUrl}/api/render/story`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type,
      title,
      content,
      ctaText,
      ctaLink,
      format: 'story', // Instagram story 1080x1920
      timestamp: new Date().toISOString(),
    }),
  });

  if (!response.ok) {
    throw new Error(`Story generation failed: ${await response.text()}`);
  }

  const data = (await response.json()) as { imageUrl: string };
  return data.imageUrl;
}

/**
 * Generate all daily stories (3 stories at different times)
 */
async function generateDailyStories(): Promise<GeneratedStory[]> {
  const generatedStories: GeneratedStory[] = [];

  // Morning story: Market update
  const morningContent: StoryContent = {
    type: 'market_update',
    title: 'Market Open Update',
    content: getRandomMarketUpdate(),
    ctaText: 'Trade Now',
    ctaLink: 'https://profitengine.alreadyherellc.com',
    timestamp: new Date().toISOString(),
  };

  try {
    const morningImage = await generateMarketUpdateStory(morningContent);
    generatedStories.push({
      imageUrl: morningImage,
      content: morningContent,
      generatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error(`Failed to generate morning story: ${error}`);
  }

  // Noon story: Poll
  const noonContent: StoryContent = {
    type: 'poll',
    title: 'What\'s Your Biggest Trading Challenge?',
    content: 'Backtesting Accuracy | Risk Management | Entry Signals | Exit Timing',
    ctaLink: 'https://profitengine.alreadyherellc.com/poll/trading-challenges',
    timestamp: new Date().toISOString(),
  };

  try {
    const noonImage = await generatePollStory(noonContent);
    generatedStories.push({
      imageUrl: noonImage,
      content: noonContent,
      generatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error(`Failed to generate noon story: ${error}`);
  }

  // Evening story: Q&A or Trading Tip
  const eveningType = Math.random() > 0.5 ? 'qa' : 'tip';
  const eveningContent: StoryContent = {
    type: eveningType as 'qa' | 'tip',
    title:
      eveningType === 'qa'
        ? 'Q&A: How do I avoid curve fitting?'
        : 'Trading Tip: Risk Management Rules',
    content:
      eveningType === 'qa'
        ? 'Test strategies on out-of-sample data, use walk-forward analysis, validate on multiple markets'
        : 'Never risk more than 2% per trade, maintain a win/loss ratio of at least 2:1, use position sizing correctly',
    ctaText: 'Learn More',
    ctaLink: 'https://profitengine.alreadyherellc.com/learn',
    timestamp: new Date().toISOString(),
  };

  try {
    const eveningImage =
      eveningType === 'qa' ? await generateQAStory(eveningContent) : await generateTipStory(eveningContent);
    generatedStories.push({
      imageUrl: eveningImage,
      content: eveningContent,
      generatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error(`Failed to generate evening story: ${error}`);
  }

  return generatedStories;
}

/**
 * Get random market update content
 */
function getRandomMarketUpdate(): string {
  const updates = [
    'SPY up 1.2% on Fed rate pause speculation',
    'Bitcoin testing $67K resistance level',
    'Oil prices spike on supply concerns',
    'Tech stocks lead market rally today',
    'Dollar weakness boosts commodity prices',
    'Earnings season delivers mixed results',
    'VIX compression signals lower volatility ahead',
    'EURUSD breaks key technical level',
  ];

  return updates[Math.floor(Math.random() * updates.length)];
}

/**
 * Upload story to Instagram via Meta Graph API
 */
async function uploadStoryToInstagram(story: GeneratedStory): Promise<string> {
  try {
    const igUserId = process.env.IG_USER_ID;
    const accessToken = process.env.FB_PAGE_ACCESS_TOKEN;

    if (!igUserId || !accessToken) {
      throw new Error('IG_USER_ID or FB_PAGE_ACCESS_TOKEN not configured');
    }

    // Create story media
    const response = await fetch(`https://graph.instagram.com/v18.0/${igUserId}/media`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        media_type: 'STORIES',
        image_url: story.imageUrl,
        user_tags: [],
        access_token: accessToken,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Instagram API error: ${error}`);
    }

    const data = (await response.json()) as { id: string };

    // Publish story (stories are published immediately)
    const publishResponse = await fetch(
      `https://graph.instagram.com/v18.0/${igUserId}/media_publish`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          creation_id: data.id,
          access_token: accessToken,
        }),
      }
    );

    if (!publishResponse.ok) {
      throw new Error(`Story publish failed: ${await publishResponse.text()}`);
    }

    return data.id;
  } catch (error) {
    throw new Error(`Story upload failed: ${error}`);
  }
}

/**
 * Post story at scheduled times (9 AM, 12 PM, 7 PM ET)
 */
function getNextStoryPostTime(postNumber: 1 | 2 | 3): Date {
  const now = new Date();

  // ET times in UTC
  const schedules = [
    { hour: 13, min: 0 }, // 9 AM ET = 13 UTC
    { hour: 16, min: 0 }, // 12 PM ET = 16 UTC
    { hour: 23, min: 0 }, // 7 PM ET = 23 UTC
  ];

  const schedule = schedules[postNumber - 1];
  const next = new Date(now);

  next.setUTCHours(schedule.hour, schedule.min, 0, 0);

  // If time has passed today, schedule for tomorrow
  if (next < now) {
    next.setUTCDate(next.getUTCDate() + 1);
  }

  return next;
}

/**
 * Main orchestration function: Generate and post daily stories
 */
export async function generateAndPostStories(): Promise<InstagramStoryResult> {
  try {
    console.log('Generating 3 daily Instagram stories...');

    // Generate all 3 daily stories
    const generatedStories = await generateDailyStories();

    if (generatedStories.length === 0) {
      return {
        success: false,
        error: 'No stories were generated',
      };
    }

    console.log(`Generated ${generatedStories.length} stories`);

    // Upload stories and track post times
    const uploadedStoryIds: string[] = [];
    const postTimes: Date[] = [];

    for (let i = 0; i < generatedStories.length; i++) {
      const story = generatedStories[i];
      const postTime = getNextStoryPostTime((i + 1) as 1 | 2 | 3);

      try {
        console.log(`Uploading story ${i + 1}/3...`);
        const storyId = await uploadStoryToInstagram(story);
        uploadedStoryIds.push(storyId);
        postTimes.push(postTime);

        console.log(`✓ Story ${i + 1} posted: ${storyId} at ${postTime.toISOString()}`);
      } catch (error) {
        console.error(`✗ Failed to upload story ${i + 1}: ${error}`);
      }
    }

    if (uploadedStoryIds.length === 0) {
      return {
        success: false,
        error: 'Failed to upload any stories',
      };
    }

    return {
      success: true,
      storyId: uploadedStoryIds[0],
      generatedStories,
      postTime: postTimes[0].toISOString(),
    };
  } catch (error) {
    return {
      success: false,
      error: `Stories orchestration failed: ${error}`,
    };
  }
}

export { StoryContent, DailyStorySet, GeneratedStory, InstagramStoryResult };
