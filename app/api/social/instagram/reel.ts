import { NextResponse } from 'next/server';
import {
  generateReelScript,
  validateReelScript,
} from '@/lib/instagram/reel-scripts';
import { createInstagramAPI } from '@/lib/instagram-graph-api';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/**
 * POST /api/social/instagram/reel
 * Generate a reel script from topic and parameters
 *
 * Request body:
 * {
 *   topic: string,           // "How Mean Reversion Made $39K"
 *   duration: 30 | 60,       // Seconds (30 or 60)
 *   tone?: 'educational' | 'entertaining'  // Default: 'educational'
 * }
 *
 * Response:
 * {
 *   ok: true,
 *   script: {
 *     id, topic, duration, tone, segments, totalDuration, textOverlays, description, hashtags, metadata
 *   }
 * }
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();

    const { topic, duration, tone = 'educational' } = body;

    // Validation
    if (!topic) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Missing required field: topic',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (!duration || (duration !== 30 && duration !== 60)) {
      return NextResponse.json(
        {
          ok: false,
          error: 'duration must be 30 or 60 seconds',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (tone !== 'educational' && tone !== 'entertaining') {
      return NextResponse.json(
        {
          ok: false,
          error: 'tone must be "educational" or "entertaining"',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (topic.length < 5 || topic.length > 200) {
      return NextResponse.json(
        {
          ok: false,
          error: 'topic must be between 5 and 200 characters',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    // Generate reel script
    const script = generateReelScript(topic, duration, tone);

    // Validate structure
    const validation = validateReelScript(script);
    if (!validation.isValid) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Generated reel script is invalid',
          details: validation.errors,
        },
        { status: 500, headers: NO_STORE }
      );
    }

    return NextResponse.json(
      {
        ok: true,
        script,
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
 * PUT /api/social/instagram/reel/publish
 * Publish reel to Instagram (requires video URL)
 *
 * Request body:
 * {
 *   reelId: string,
 *   videoUrl: string,
 *   caption: string,
 *   thumbnail?: string
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
    const { reelId, videoUrl, caption, thumbnail } = body;

    if (!reelId || !videoUrl || !caption) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Missing required fields: reelId, videoUrl, caption',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    // Validate video URL is accessible
    if (!videoUrl.startsWith('http://') && !videoUrl.startsWith('https://')) {
      return NextResponse.json(
        {
          ok: false,
          error: 'videoUrl must be a valid HTTP(S) URL',
        },
        { status: 400, headers: NO_STORE }
      );
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

      // Upload reel
      const response = await api.uploadReel(videoUrl, caption, thumbnail);

      return NextResponse.json(
        {
          ok: true,
          mediaId: response.id,
          status: response.status,
          message:
            'Reel is being processed. Video processing may take 1-5 minutes. Check back later.',
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
          action: 'Ensure video is mp4 format, under 90 seconds, and URL is accessible',
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

/**
 * GET /api/social/instagram/reel/status
 * Check status of reel upload
 *
 * Query params:
 * - mediaId: string (required)
 *
 * Response:
 * {
 *   ok: true,
 *   mediaId: string,
 *   status: 'PROCESSING' | 'FINISHED' | 'ERROR'
 * }
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const mediaId = searchParams.get('mediaId');

    if (!mediaId) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Missing required query parameter: mediaId',
        },
        { status: 400, headers: NO_STORE }
      );
    }

    if (!process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || !process.env.INSTAGRAM_ACCESS_TOKEN) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Instagram API not configured',
        },
        { status: 503, headers: NO_STORE }
      );
    }

    try {
      const api = createInstagramAPI();
      const status = await api.getMediaStatus(mediaId);

      return NextResponse.json(
        {
          ok: true,
          mediaId: status.id,
          status: status.status || 'UNKNOWN',
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
