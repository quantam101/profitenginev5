/**
 * Instagram Story Templates Generator
 * Daily story templates for trading content
 * 3 template types: Market update, Poll, Engagement question
 */

export interface StoryTemplate {
  id: string;
  type: 'market_update' | 'poll' | 'engagement';
  title: string;
  content: string;
  visualDescription: string;
  duration: number; // seconds
  interactiveElements?: InteractiveElement[];
  textOverlays: TextOverlayStory[];
  backgroundColor?: string;
  metadata: {
    createdAt: string;
    bestTimeToPost?: string;
    estimatedEngagementRate?: number;
  };
}

export interface InteractiveElement {
  type: 'poll' | 'question' | 'slider' | 'quiz';
  text: string;
  options?: string[];
  position?: 'center' | 'bottom';
}

export interface TextOverlayStory {
  text: string;
  position: 'top' | 'middle' | 'bottom';
  fontSize: 'small' | 'medium' | 'large';
  color: string;
  backgroundColor?: string;
}

export interface StoryCampaign {
  id: string;
  date: string;
  stories: StoryTemplate[];
  totalDuration: number;
  postingSchedule: PostingTime[];
  theme: string;
}

export interface PostingTime {
  storyIndex: number;
  timeOfDay: 'morning' | 'midday' | 'evening';
  hour: number;
  minute: number;
}

/**
 * Generate 3 daily stories for consistent posting
 * Returns: 1 market update, 1 poll, 1 engagement story
 */
export function generateDailyStories(
  marketUpdate?: MarketData,
  engagementPrompt?: string
): StoryCampaign {
  const stories: StoryTemplate[] = [];
  const date = new Date().toISOString().split('T')[0];

  // Story 1: Market Update (8 AM / Morning)
  stories.push(generateMarketUpdateStory(marketUpdate));

  // Story 2: Poll (1 PM / Midday)
  stories.push(generatePollStory());

  // Story 3: Engagement (6 PM / Evening)
  stories.push(generateEngagementStory(engagementPrompt));

  const postingSchedule: PostingTime[] = [
    { storyIndex: 0, timeOfDay: 'morning', hour: 8, minute: 0 },
    { storyIndex: 1, timeOfDay: 'midday', hour: 13, minute: 0 },
    { storyIndex: 2, timeOfDay: 'evening', hour: 18, minute: 0 },
  ];

  return {
    id: `campaign-${date}-${Date.now()}`,
    date,
    stories,
    totalDuration: stories.reduce((sum, s) => sum + s.duration, 0),
    postingSchedule,
    theme: 'Trading Strategy Daily',
  };
}

/**
 * Market Update Story Template
 * Single slide: "NVDA breaking $140 | Momentum setup active"
 */
export interface MarketData {
  symbol: string;
  price: number;
  changePercent: number;
  setupDescription: string;
  actionable?: boolean;
}

function generateMarketUpdateStory(marketData?: MarketData): StoryTemplate {
  const symbol = marketData?.symbol || 'SPY';
  const price = marketData?.price || 425.5;
  const change = marketData?.changePercent || 1.2;
  const setup = marketData?.setupDescription || 'Momentum setup forming';

  return {
    id: `story-market-${Date.now()}`,
    type: 'market_update',
    title: `${symbol} Trading Setup`,
    content: `📈 ${symbol} breaking through key level\n\nPrice: $${price}\nChange: ${change > 0 ? '+' : ''}${change}%\n\nSetup: ${setup}\n\nStatus: ${marketData?.actionable ? '⚡ ACTIVE' : '👀 Watching'}`,
    visualDescription:
      'Clean design with large symbol name (SPY, NVDA, etc), current price in huge font, green or red color based on direction, momentum chart snippet, key level marked with horizontal line',
    duration: 5,
    textOverlays: [
      {
        text: `${symbol} Momentum Setup`,
        position: 'top',
        fontSize: 'large',
        color: '#ffffff',
        backgroundColor: '#000000cc',
      },
      {
        text: `$${price} | ${change > 0 ? '📈' : '📉'} ${change}%`,
        position: 'middle',
        fontSize: 'large',
        color: change > 0 ? '#4ecdc4' : '#ff6b6b',
      },
      {
        text: setup,
        position: 'bottom',
        fontSize: 'medium',
        color: '#ffffff',
        backgroundColor: '#1a1a2ecc',
      },
    ],
    backgroundColor: '#0f3460',
    metadata: {
      createdAt: new Date().toISOString(),
      bestTimeToPost: '8:00 AM ET',
      estimatedEngagementRate: 0.08, // 8% for market updates
    },
  };
}

/**
 * Poll Story Template
 * Interactive: "Will market close green? Vote below"
 */
function generatePollStory(): StoryTemplate {
  const pollOptions = [
    'Yes, close green',
    'No, close red',
    'Neutral/Flat',
  ];

  return {
    id: `story-poll-${Date.now()}`,
    type: 'poll',
    title: 'Daily Market Poll',
    content:
      'Will the market close green today?\n\nTap to vote →',
    visualDescription:
      'Market chart showing daily movement so far, poll results animation at bottom, vibrant colors for yes/no options',
    duration: 8,
    interactiveElements: [
      {
        type: 'poll',
        text: 'Will SPY close green today?',
        options: pollOptions,
        position: 'bottom',
      },
    ],
    textOverlays: [
      {
        text: 'Market Prediction Poll',
        position: 'top',
        fontSize: 'large',
        color: '#ffffff',
        backgroundColor: '#000000cc',
      },
      {
        text: 'What\'s your prediction?',
        position: 'middle',
        fontSize: 'medium',
        color: '#4ecdc4',
      },
      {
        text: 'Tap to vote ↓',
        position: 'bottom',
        fontSize: 'medium',
        color: '#ffffff',
        backgroundColor: '#e94560cc',
      },
    ],
    backgroundColor: '#16213e',
    metadata: {
      createdAt: new Date().toISOString(),
      bestTimeToPost: '1:00 PM ET',
      estimatedEngagementRate: 0.15, // 15% for polls (highest engagement)
    },
  };
}

/**
 * Engagement Question Story Template
 * Q&A: "What's your biggest trading mistake?"
 */
function generateEngagementStory(customPrompt?: string): StoryTemplate {
  const prompts = [
    "What's your biggest trading mistake?",
    'Backtest returns or live returns—which do you trust?',
    'What strategy have you tested most?',
    'How long until you go live after backtesting?',
    'What makes a strategy actually profitable?',
    'Slippage or emotions—which costs you more?',
    'Most shocking backtest-to-live gap you\'ve seen?',
  ];

  const selectedPrompt = customPrompt || prompts[Math.floor(Math.random() * prompts.length)];

  return {
    id: `story-engagement-${Date.now()}`,
    type: 'engagement',
    title: 'Daily Engagement Question',
    content: selectedPrompt,
    visualDescription:
      'Question centered on screen with soft gradient background, call-to-action arrow pointing to question sticker area, trading theme colors',
    duration: 10,
    interactiveElements: [
      {
        type: 'question',
        text: selectedPrompt,
        position: 'center',
      },
    ],
    textOverlays: [
      {
        text: selectedPrompt,
        position: 'middle',
        fontSize: 'large',
        color: '#ffffff',
        backgroundColor: '#000000cc',
      },
      {
        text: 'Reply with your answer →',
        position: 'bottom',
        fontSize: 'medium',
        color: '#4ecdc4',
        backgroundColor: '#1a1a2ecc',
      },
    ],
    backgroundColor: '#0f3460',
    metadata: {
      createdAt: new Date().toISOString(),
      bestTimeToPost: '6:00 PM ET',
      estimatedEngagementRate: 0.12, // 12% for questions
    },
  };
}

/**
 * Generate themed weekly stories (7 days)
 */
export function generateWeeklyStories(): StoryCampaign[] {
  const campaigns: StoryCampaign[] = [];

  const weekThemes = [
    {
      date: getDateString(0),
      theme: 'Mean Reversion Week',
      update: {
        symbol: 'RSI Levels',
        price: 28,
        changePercent: 2.1,
        setupDescription: 'Oversold setup forming',
        actionable: true,
      },
      prompt: 'Ever traded mean reversion?',
    },
    {
      date: getDateString(1),
      theme: 'Momentum Strategies',
      update: {
        symbol: 'MACD Cross',
        price: 15,
        changePercent: 1.8,
        setupDescription: 'Bullish crossover detected',
        actionable: true,
      },
      prompt: 'What\'s your favorite momentum indicator?',
    },
    {
      date: getDateString(2),
      theme: 'Risk Management Focus',
      update: {
        symbol: 'Position Size',
        price: 2.5,
        changePercent: 0.5,
        setupDescription: 'Risk per trade optimal',
        actionable: false,
      },
      prompt: 'How do you calculate position size?',
    },
    {
      date: getDateString(3),
      theme: 'Backtest Reality Check',
      update: {
        symbol: 'Slippage Cost',
        price: 8000,
        changePercent: -3.2,
        setupDescription: 'Hidden costs revealed',
        actionable: false,
      },
      prompt: 'Biggest backtest-to-live gap you\'ve seen?',
    },
    {
      date: getDateString(4),
      theme: 'Live Trading Lessons',
      update: {
        symbol: 'Execution',
        price: 0.98,
        changePercent: 0.2,
        setupDescription: 'Fill quality improved',
        actionable: true,
      },
      prompt: 'What\'s the biggest difference between backtest and live?',
    },
    {
      date: getDateString(5),
      theme: 'Strategy Diversification',
      update: {
        symbol: 'Correlation',
        price: 0.15,
        changePercent: -0.8,
        setupDescription: 'Low correlation achieved',
        actionable: true,
      },
      prompt: 'How many strategies do you actively trade?',
    },
    {
      date: getDateString(6),
      theme: 'Weekly Recap & Plans',
      update: {
        symbol: 'Weekly P&L',
        price: 2400,
        changePercent: 5.2,
        setupDescription: 'Solid week executed',
        actionable: false,
      },
      prompt: 'What\'s your biggest win this week?',
    },
  ];

  weekThemes.forEach((theme, idx) => {
    const campaign = generateDailyStories(theme.update, theme.prompt);
    campaigns.push(campaign);
  });

  return campaigns;
}

/**
 * Batch generate stories for multiple days
 */
export function generateStoriesBatch(dayCount: number): StoryCampaign[] {
  const campaigns: StoryCampaign[] = [];
  for (let i = 0; i < dayCount; i++) {
    const campaign = generateDailyStories();
    campaigns.push(campaign);
  }
  return campaigns;
}

/**
 * Helper: Get date string offset from today
 */
function getDateString(daysOffset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysOffset);
  return date.toISOString().split('T')[0];
}

/**
 * Validate story campaign structure
 */
export function validateStoryCampaign(campaign: StoryCampaign): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Check we have 3 stories
  if (campaign.stories.length !== 3) {
    errors.push(`Campaign should have 3 stories, has ${campaign.stories.length}`);
  }

  // Check story types are correct
  const types = campaign.stories.map(s => s.type);
  if (!types.includes('market_update')) {
    errors.push('Campaign missing market_update story');
  }
  if (!types.includes('poll')) {
    errors.push('Campaign missing poll story');
  }
  if (!types.includes('engagement')) {
    errors.push('Campaign missing engagement story');
  }

  // Check posting schedule
  if (campaign.postingSchedule.length !== 3) {
    errors.push(
      `Posting schedule should have 3 slots, has ${campaign.postingSchedule.length}`
    );
  }

  campaign.stories.forEach((story, idx) => {
    if (!story.title || story.title.trim().length === 0) {
      errors.push(`Story ${idx + 1}: Missing title`);
    }
    if (!story.content || story.content.trim().length === 0) {
      errors.push(`Story ${idx + 1}: Missing content`);
    }
    if (story.duration < 5 || story.duration > 10) {
      errors.push(`Story ${idx + 1}: Duration ${story.duration}s outside 5-10s range`);
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
  };
}
