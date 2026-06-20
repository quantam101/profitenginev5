import { NextResponse } from 'next/server';
import {
  generateCarouselFromThread,
  validateCarousel,
  type BacktestData,
} from '@/lib/instagram/carousel-generator';
import { createInstagramAPI } from '@/lib/instagram-graph-api';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/**
 * POST /api/social/instagram/carousel
 * Generate a carousel post structure from thread text or strategy data
 *
 * Request body:
 * {
 *   threadText: string,
 *   strategy: string,
 *   backtestData?: {
 *     strategyName: string,
 *     returns: number,
 *     winRate: number,
 *     maxDrawdown: number,
 *     sharpeRatio: number,
 *     trades: number,
 *     period: string
 *   }
 * }
 *
 * Response:
 * {
 *   ok: true,
 *   carousel: {
 *     id, strategy, title, description, slides, caption, hashtags, estimatedEngagement, metadata
 *   }
 * }
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();

    const { threadText, strategy, backtestData } = body;

    // Validation
    if (!threadText || !strategy) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Missing required fields: threadText, strategy',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (threadText.length < 20) {
      return NextResponse.json(
        {
          ok: false,
          error: 'threadText must be at least 20 characters',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    // Generate carousel
    const carousel = generateCarouselFromThread(
      threadText,
      strategy,
      backtestData as BacktestData | undefined
    );

    // Validate structure
    const validation = validateCarousel(carousel);
    if (!validation.isValid) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Generated carousel structure is invalid',
          details: validation.errors,
        },
        { status: 500, headers: NO_STORE }
      );
    }

    return NextResponse.json(
      {
        ok: true,
        carousel,
        validation: { isValid: true },
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

/**
 * POST /api/social/instagram/carousel/publish
 * Publish carousel to Instagram (requires image URLs for slides)
 *
 * Request body:
 * {
 *   carouselId: string,
 *   slides: Array<{ imageUrl: string, caption?: string }>,
 *   caption: string
 * }
 *
 * Response:
 * {
 *   ok: true,
 *   mediaId: string,
 *   status: 'PROCESSING'
 * }
 */
export async function PUT(request: Request) {
  try {
    // Check if Instagram API is configured
    if (!process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || !process.env.INSTAGRAM_ACCESS_TOKEN) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Instagram API not configured',
          action: 'Add INSTAGRAM_BUSINESS_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN to environment',
        },
        { status: 503, headers: NO_STORE }
      );
    }

    const body = await request.json();
    const { carouselId, slides, caption } = body;

    if (!carouselId || !slides || !caption) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Missing required fields: carouselId, slides, caption',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (!Array.isArray(slides) || slides.length < 2 || slides.length > 10) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Carousel must have 2-10 slides',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    // Validate slide structure
    for (let i = 0; i < slides.length; i++) {
      if (!slides[i].imageUrl) {
        return NextResponse.json(
          {
            ok: false,
            error: `Slide ${i + 1} missing imageUrl`,
          },
          { status: 400, headers: NO_STORE }
        );
      }
    }

    try {
      const api = createInstagramAPI();

      // Validate connection first
      const isConnected = await api.validateConnection();
      if (!isConnected) {
        return NextResponse.json(
          {
            ok: false,
            error: 'Instagram API connection failed',
            action: 'Verify INSTAGRAM_ACCESS_TOKEN is valid',
          },
          { status: 401, headers: NO_STORE }
        );
      }

      // Upload carousel
      const response = await api.uploadCarousel(slides, caption);

      return NextResponse.json(
        {
          ok: true,
          mediaId: response.id,
          status: response.status,
          message: 'Carousel is being processed. Check status shortly.',
        },
        { status: 200, headers: NO_STORE }
      );
    } catch (apiError) {
      const message =
        apiError instanceof Error ? apiError.message : 'Instagram API error';
      return NextResponse.json(
        {
          ok: false,
          error: message,
          action: 'Check that slide URLs are accessible and valid',
        },
        { status: 502, headers: NO_STORE }
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
