import { NextResponse } from 'next/server';
import {
  generateCarouselFromThread,
  validateCarousel,
  type BacktestData,
} from '@/lib/instagram/carousel-generator';
import {
  generateReelScript,
  validateReelScript,
} from '@/lib/instagram/reel-scripts';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/**
 * POST /api/social/cross-post
 * Auto-generate carousel/reel scripts when cross-posting to Instagram
 * Automatically creates Instagram content variants from Threads/Twitter content
 *
 * Request body:
 * {
 *   platform: 'threads' | 'twitter',
 *   content: string,                        // The original post text
 *   strategy?: string,                      // Trading strategy name (if applicable)
 *   type: 'thread' | 'post',                // Type of original content
 *   title?: string,                         // Optional title/hook
 *   backtestData?: { ... }                  // Optional backtest metrics
 * }
 *
 * Response:
 * {
 *   ok: true,
 *   crossPostPlan: {
 *     carousel: { structure, ready: boolean },
 *     reel: { script, ready: boolean },
 *     schedule: { carousel, reel },
 *     approval: { required: true, message: '...' }
 *   }
 * }
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();

    const {
      platform,
      content,
      strategy,
      type,
      title,
      backtestData,
    } = body;

    // Validation
    if (!platform || !['threads', 'twitter'].includes(platform)) {
      return NextResponse.json(
        {
          ok: false,
          error: 'platform must be "threads" or "twitter"',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (!content || content.length < 20) {
      return NextResponse.json(
        {
          ok: false,
          error: 'content must be at least 20 characters',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (!type || !['thread', 'post'].includes(type)) {
      return NextResponse.json(
        {
          ok: false,
          error: 'type must be "thread" or "post"',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    try {
      // Generate carousel from thread content
      let carousel = null;
      let carouselValid = false;

      if (strategy) {
        carousel = generateCarouselFromThread(
          content,
          strategy,
          backtestData as BacktestData | undefined
        );
        const carouselValidation = validateCarousel(carousel);
        carouselValid = carouselValidation.isValid;

        if (!carouselValid) {
          console.warn('Carousel validation failed:', carouselValidation.errors);
        }
      }

      // Generate reel script from content
      const reelTopic = title || extractMainTopicFromContent(content);
      const reel = generateReelScript(reelTopic, 60, 'educational');
      const reelValidation = validateReelScript(reel);
      const reelValid = reelValidation.isValid;

      if (!reelValid) {
        console.warn('Reel validation failed:', reelValidation.errors);
      }

      // Calculate recommended posting times (24 hours after original post)
      const now = new Date();
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);

      const schedule = {
        carousel: {
          recommendedTime: new Date(tomorrow.getTime() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours after tomorrow
          note: 'Post carousel 24-36 hours after Threads post for maximum reach',
        },
        reel: {
          recommendedTime: new Date(tomorrow.getTime() + 12 * 60 * 60 * 1000).toISOString(), // 12 hours after tomorrow
          note: 'Reels get 67% higher reach - post mid-day for peak engagement',
        },
        story: {
          recommendedTime: new Date(tomorrow.getTime() + 18 * 60 * 60 * 1000).toISOString(), // 6 PM tomorrow
          note: 'Story pointing to carousel/reel drives traffic to both',
        },
      };

      // Build cross-post plan
      const crossPostPlan = {
        source: {
          platform,
          type,
          characterCount: content.length,
        },
        carousel: carousel ? {
          id: carousel.id,
          title: carousel.title,
          slideCount: carousel.slides.length,
          ready: carouselValid,
          status: carouselValid ? 'READY_FOR_DESIGN' : 'NEEDS_REVIEW',
          errors: carouselValid ? [] : ['Carousel structure needs review before posting'],
        } : null,
        reel: {
          id: reel.id,
          topic: reel.topic,
          duration: reel.duration,
          ready: reelValid,
          status: reelValid ? 'READY_FOR_PRODUCTION' : 'NEEDS_REVIEW',
          errors: reelValid ? [] : ['Reel script needs review before production'],
        },
        schedule,
        approval: {
          required: true,
          message:
            'Both carousel and reel need manual review before Instagram posting. Review designs/video and approve for publishing.',
          workflowSteps: [
            '1. Review carousel slides and design them in Canva/Figma',
            '2. Get carousel image URLs (upload to cloud storage)',
            '3. Review reel script and produce video (AI or screen recording)',
            '4. Get reel video URL (upload to cloud storage)',
            '5. Use /api/social/instagram/carousel/publish with image URLs',
            '6. Use /api/social/instagram/reel/publish with video URL',
            '7. Schedule stories to cross-promote carousel and reel',
          ],
        },
        ftcCompliance: {
          required: true,
          message: 'All Instagram posts with affiliate links must include FTC disclosure',
          disclosure: '#ad or #sponsored required in caption if applicable',
        },
        estimatedReach: {
          carousel: 2500,
          reel: 3500,
          stories: 1200,
          totalImpressions: 7200,
        },
      };

      return NextResponse.json(
        {
          ok: true,
          crossPostPlan,
          fullContent: {
            carousel,
            reel,
          },
        },
        { status: 200, headers: NO_STORE }
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to generate cross-post plan';
      return NextResponse.json(
        {
          ok: false,
          error: message,
        },
        { status: 500, headers: NO_STORE }
      );
    }
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { ok: false, error: message },
      { status: 500, headers: NO_STORE }
    );
  }
}

/**
 * Extract main topic from content text
 */
function extractMainTopicFromContent(content: string): string {
  const lines = content.split('\n');
  const firstLine = lines[0] || 'Trading Strategy';

  // Truncate to reasonable length for reel topic
  if (firstLine.length > 100) {
    return firstLine.substring(0, 97) + '...';
  }

  return firstLine;
}

/**
 * GET /api/social/cross-post/preview
 * Get a preview of what Instagram content would look like from Threads content
 *
 * Query params:
 * - threadText: string (URL encoded)
 * - strategy?: string
 *
 * Response:
 * {
 *   ok: true,
 *   preview: {
 *     carousel: { slides: [...] },
 *     reel: { segments: [...], textOverlays: [...] },
 *   }
 * }
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const threadText = searchParams.get('threadText');
    const strategy = searchParams.get('strategy') || 'Trading Strategy';

    if (!threadText || threadText.length < 20) {
      return NextResponse.json(
        {
          ok: false,
          error: 'threadText query parameter required and must be at least 20 characters',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    const carousel = generateCarouselFromThread(threadText, strategy);
    const reel = generateReelScript(strategy, 60, 'educational');

    const preview = {
      carousel: {
        title: carousel.title,
        slideCount: carousel.slides.length,
        slides: carousel.slides.map((s, idx) => ({
          number: s.slideNumber,
          title: s.title,
          keyPoints: s.keyPoints.slice(0, 2), // Preview first 2 points
          textOverlay: s.textOverlay,
        })),
      },
      reel: {
        topic: reel.topic,
        duration: reel.duration,
        segments: reel.segments.map(seg => ({
          number: seg.segmentNumber,
          duration: seg.duration,
          preview: seg.voiceover.substring(0, 50) + '...',
        })),
      },
    };

    return NextResponse.json(
      {
        ok: true,
        preview,
      },
      { status: 200, headers: NO_STORE }
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { ok: false, error: message },
      { status: 500, headers: NO_STORE }
    );
  }
}
