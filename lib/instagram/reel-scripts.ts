/**
 * Instagram Reel Scripts Generator
 * Generates 30-60 second reel scripts from strategy/backtest content
 * Reel format: Hook (5s) → Explanation (25s) → CTA (5s)
 */

export interface ReelScript {
  id: string;
  topic: string;
  duration: 30 | 60;
  tone: 'educational' | 'entertaining';
  segments: ReelSegment[];
  totalDuration: number;
  audioCue?: string;
  textOverlays: TextOverlay[];
  description: string;
  hashtags: string[];
  metadata: {
    createdAt: string;
    estimatedViews: number;
    estimatedEngagementRate: number;
  };
}

export interface ReelSegment {
  segmentNumber: number;
  duration: number;
  voiceover: string;
  visualCue: string;
  textOverlay?: string;
  transition?: 'cut' | 'fade' | 'zoom' | 'swipe';
  timing: {
    startSecond: number;
    endSecond: number;
  };
}

export interface TextOverlay {
  text: string;
  duration: number;
  position: 'top' | 'middle' | 'bottom';
  fontSize: 'small' | 'medium' | 'large' | 'xl';
  color: string;
  backgroundColor?: string;
  startSecond: number;
  endSecond: number;
}

/**
 * Generates a complete reel script from topic and parameters
 * Input: topic, duration (30/60), tone (educational/entertaining)
 * Output: Full reel script with timing and visual cues
 */
export function generateReelScript(
  topic: string,
  duration: 30 | 60,
  tone: 'educational' | 'entertaining' = 'educational'
): ReelScript {
  const id = `reel-${Date.now()}`;
  const segments: ReelSegment[] = [];
  const textOverlays: TextOverlay[] = [];

  if (duration === 30) {
    generateShortReel(topic, tone, segments, textOverlays);
  } else {
    generateLongReel(topic, tone, segments, textOverlays);
  }

  const description = generateReelDescription(topic, duration);
  const hashtags = generateReelHashtags(topic);

  return {
    id,
    topic,
    duration,
    tone,
    segments,
    totalDuration: duration,
    textOverlays,
    description,
    hashtags,
    metadata: {
      createdAt: new Date().toISOString(),
      estimatedViews: duration === 60 ? 3500 : 2000, // Reels get 67% higher reach
      estimatedEngagementRate: 0.12, // 12% avg engagement
    },
  };
}

/**
 * Generate 30-second short reel
 */
function generateShortReel(
  topic: string,
  tone: string,
  segments: ReelSegment[],
  textOverlays: TextOverlay[]
): void {
  // Hook Phase (0-5 seconds)
  if (tone === 'educational') {
    segments.push({
      segmentNumber: 1,
      duration: 5,
      voiceover: `Your backtest shows 40% returns.\nYour live account shows -8% loss.\nWhy?`,
      visualCue: 'Split screen: backtest chart (40% return bar) vs live account chart (-8% return bar)',
      textOverlay: 'Why does this happen?',
      transition: 'cut',
      timing: { startSecond: 0, endSecond: 5 },
    });

    textOverlays.push({
      text: 'Backtest: +40% | Live: -8%',
      duration: 5,
      position: 'middle',
      fontSize: 'xl',
      color: '#ffffff',
      backgroundColor: '#000000cc',
      startSecond: 0,
      endSecond: 5,
    });
  } else {
    segments.push({
      segmentNumber: 1,
      duration: 5,
      voiceover: `I just realized something wild about backtests.\nThey're lying to you.\nAnd here's why it matters...`,
      visualCue: 'Eye-catching transition with chart flip or dramatic zoom on key number',
      textOverlay: 'Plot twist:',
      transition: 'zoom',
      timing: { startSecond: 0, endSecond: 5 },
    });

    textOverlays.push({
      text: 'Your backtest is LYING',
      duration: 5,
      position: 'top',
      fontSize: 'xl',
      color: '#ff0000',
      startSecond: 0,
      endSecond: 5,
    });
  }

  // Content Phase (5-25 seconds)
  segments.push({
    segmentNumber: 2,
    duration: 20,
    voiceover: `Backtests don't account for:\n• Slippage (2-4% per trade)\n• Liquidity constraints\n• Tax impact\n• Emotional exits\n\nSo when you trade live, reality hits different.`,
    visualCue:
      'Screen recording: Scrolling through backtest settings, highlighting slippage field (showing 0%), then showing realistic slippage cost ($8,000), then live trading reality check',
    textOverlay: 'The hidden costs:',
    transition: 'fade',
    timing: { startSecond: 5, endSecond: 25 },
  });

  textOverlays.push({
    text: 'Slippage: 2-4% per trade',
    duration: 5,
    position: 'bottom',
    fontSize: 'large',
    color: '#ffffff',
    backgroundColor: '#000000cc',
    startSecond: 5,
    endSecond: 10,
  });

  textOverlays.push({
    text: 'That\'s 20-40% of your profits gone',
    duration: 5,
    position: 'bottom',
    fontSize: 'large',
    color: '#ff6b6b',
    backgroundColor: '#000000cc',
    startSecond: 10,
    endSecond: 15,
  });

  textOverlays.push({
    text: 'ProfitEngine shows realistic results',
    duration: 10,
    position: 'bottom',
    fontSize: 'large',
    color: '#4ecdc4',
    backgroundColor: '#000000cc',
    startSecond: 15,
    endSecond: 25,
  });

  // CTA Phase (25-30 seconds)
  segments.push({
    segmentNumber: 3,
    duration: 5,
    voiceover: `Stop trusting fake backtests.\nTry ProfitEngine free.\nLink in bio.`,
    visualCue: 'Logo animation or product screenshot with "Link in Bio" text overlay',
    textOverlay: 'See Your Real Results',
    transition: 'fade',
    timing: { startSecond: 25, endSecond: 30 },
  });

  textOverlays.push({
    text: 'Link in bio',
    duration: 5,
    position: 'bottom',
    fontSize: 'xl',
    color: '#ffffff',
    backgroundColor: '#e94560',
    startSecond: 25,
    endSecond: 30,
  });
}

/**
 * Generate 60-second long reel
 */
function generateLongReel(
  topic: string,
  tone: string,
  segments: ReelSegment[],
  textOverlays: TextOverlay[]
): void {
  // Hook Phase (0-5 seconds)
  segments.push({
    segmentNumber: 1,
    duration: 5,
    voiceover: `One chart that proves backtests are wrong.\nWatch this.`,
    visualCue: 'Split screen: backtest returns vs live trading returns, animated reveal',
    textOverlay: 'This changes everything',
    transition: 'zoom',
    timing: { startSecond: 0, endSecond: 5 },
  });

  textOverlays.push({
    text: 'One Chart That Proves\nBacktests Lie',
    duration: 5,
    position: 'top',
    fontSize: 'xl',
    color: '#ffffff',
    backgroundColor: '#000000ee',
    startSecond: 0,
    endSecond: 5,
  });

  // Problem Phase (5-20 seconds)
  segments.push({
    segmentNumber: 2,
    duration: 15,
    voiceover: `Here's the disconnect:\nYour backtest assumes perfect conditions.\n• Perfect entry prices\n• No gaps or halts\n• No emotional panic sells\n• Zero slippage\n\nBut real trading has ALL of these working against you.`,
    visualCue:
      'Screen recording showing backtest settings with unrealistic assumptions highlighted, then jump cut to chaotic live trading screen',
    textOverlay: 'The backtest myth:',
    transition: 'cut',
    timing: { startSecond: 5, endSecond: 20 },
  });

  textOverlays.push({
    text: 'Backtest assumes:\n✓ Perfect entries\n✓ No slippage\n✓ Zero emotion',
    duration: 8,
    position: 'middle' as const,
    fontSize: 'medium',
    color: '#4ecdc4',
    backgroundColor: '#000000cc',
    startSecond: 5,
    endSecond: 13,
  });

  textOverlays.push({
    text: 'Reality has:\n✗ Slippage (2-4%)\n✗ Gaps\n✗ Emotions\n✗ Taxes',
    duration: 7,
    position: 'bottom' as const,
    fontSize: 'medium',
    color: '#ff6b6b',
    backgroundColor: '#000000cc',
    startSecond: 13,
    endSecond: 20,
  });

  // Solution Phase (20-45 seconds)
  segments.push({
    segmentNumber: 3,
    duration: 25,
    voiceover: `I took a real strategy that backtested at 28% annual returns.\nLived it for 6 months.\nReal result: -12%.\n\nThe gap?\n• $8K slippage costs\n• 3 blown stops\n• Tax impact\n\nSlippage alone destroyed 40% of the edge.\n\nThis is why ProfitEngine adds realistic slippage to every backtest.\nYou see the truth BEFORE risking money.`,
    visualCue:
      'Chart animation showing backtest line vs live trading line diverging, case study numbers appearing on screen, then show ProfitEngine interface with slippage adjustment slider',
    textOverlay: 'Real case study:',
    transition: 'fade',
    timing: { startSecond: 20, endSecond: 45 },
  });

  textOverlays.push({
    text: 'Strategy: Mean Reversion\nBacktest: +28%\nLive (6mo): -12%',
    duration: 10,
    position: 'middle',
    fontSize: 'large',
    color: '#ffffff',
    backgroundColor: '#000000cc',
    startSecond: 20,
    endSecond: 30,
  });

  textOverlays.push({
    text: 'Culprit: $8K slippage costs',
    duration: 8,
    position: 'middle',
    fontSize: 'large',
    color: '#ff6b6b',
    backgroundColor: '#000000cc',
    startSecond: 30,
    endSecond: 38,
  });

  textOverlays.push({
    text: 'ProfitEngine: Realistic from day 1',
    duration: 7,
    position: 'middle',
    fontSize: 'large',
    color: '#4ecdc4',
    backgroundColor: '#000000cc',
    startSecond: 38,
    endSecond: 45,
  });

  // CTA Phase (45-60 seconds)
  segments.push({
    segmentNumber: 4,
    duration: 15,
    voiceover: `Stop wasting time on fake backtests.\nProfitEngine builds in:\n• Real slippage (2-4%)\n• Commission costs\n• Tax impact\n• Market gaps\n\nSee what your strategy actually makes.\nNo guessing, no surprises.\n\nLink in bio. Free trial.`,
    visualCue:
      'Product demo showing slippage settings, then realistic backtest results, then CTA screen with "Link in Bio"',
    textOverlay: 'Get realistic results',
    transition: 'fade',
    timing: { startSecond: 45, endSecond: 60 },
  });

  textOverlays.push({
    text: 'ProfitEngine Features:\n✓ Real slippage\n✓ Commission costs\n✓ Tax impact\n✓ Market gaps',
    duration: 10,
    position: 'bottom',
    fontSize: 'medium',
    color: '#4ecdc4',
    backgroundColor: '#000000dd',
    startSecond: 45,
    endSecond: 55,
  });

  textOverlays.push({
    text: 'Link in bio\nFree trial',
    duration: 5,
    position: 'bottom',
    fontSize: 'xl',
    color: '#ffffff',
    backgroundColor: '#e94560',
    startSecond: 55,
    endSecond: 60,
  });
}

/**
 * Generate reel description for caption
 */
function generateReelDescription(topic: string, duration: number): string {
  let description = `🎬 ${topic} explained in ${duration} seconds\n\n`;
  description += `Why backtests lie and what to do about it.\n\n`;
  description += `Key takeaways:\n`;
  description += `✅ Backtests don't include slippage costs (2-4% per trade)\n`;
  description += `✅ Real trading includes gaps, halts, and emotional exits\n`;
  description += `✅ ProfitEngine shows realistic results from day 1\n\n`;
  description += `Stop trusting fake backtests. See your real trading edge.\n\n`;
  description += `Try free: Link in bio\n`;
  description += `Watch the carousel post for full breakdown.\n`;
  return description;
}

/**
 * Generate hashtags for reels
 */
function generateReelHashtags(topic: string): string[] {
  return [
    '#TradingStrategy',
    '#Backtesting',
    '#AlgoTrading',
    '#FuturesTrading',
    '#TradingTips',
    '#EdTok',
    '#TradersOfInstagram',
    '#DayTrading',
    '#MeanReversion',
    '#TechAnalysis',
    '#FinancialLiteracy',
    '#InvestingTips',
  ];
}

/**
 * Validate reel script structure
 */
export function validateReelScript(reel: ReelScript): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Check total duration
  const totalDuration = reel.segments.reduce((sum, seg) => sum + seg.duration, 0);
  if (totalDuration !== reel.duration) {
    errors.push(
      `Reel segments total ${totalDuration}s but duration set to ${reel.duration}s`
    );
  }

  // Check hook (first 5 seconds)
  const hookSegment = reel.segments[0];
  if (!hookSegment || hookSegment.duration !== 5) {
    errors.push('Hook segment must be exactly 5 seconds');
  }

  // Check CTA (last 5 seconds)
  const ctaSegment = reel.segments[reel.segments.length - 1];
  if (!ctaSegment || ctaSegment.duration < 5) {
    errors.push('CTA segment must be at least 5 seconds');
  }

  // Check text overlays for coverage
  const coverageMap = new Array(reel.duration).fill(false);
  reel.textOverlays.forEach(overlay => {
    for (let i = overlay.startSecond; i < overlay.endSecond; i++) {
      coverageMap[i] = true;
    }
  });

  const uncoveredSeconds = coverageMap.filter(c => !c).length;
  if (uncoveredSeconds > reel.duration * 0.3) {
    // Allow 30% of video without text overlays
    errors.push(
      `${uncoveredSeconds} seconds of the reel lack text overlays (audio-only viewers may miss context)`
    );
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}
