/**
 * API ENDPOINTS: Instagram Reels Automation
 *
 * POST   /api/automation/instagram/generate     — Generate single reel from script
 * POST   /api/automation/instagram/batch        — Generate multiple reels in batch
 * GET    /api/automation/instagram/status       — Get reel publishing status
 * GET    /api/automation/instagram/metrics      — Fetch engagement metrics
 * GET    /api/automation/instagram/list         — List all reels metadata
 * POST   /api/automation/instagram/webhook      — Handle Instagram webhook callbacks
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Generate single reel
 * POST /api/automation/instagram/generate
 * {
 *   "title": "5 Passive Income Streams",
 *   "hook": "Did you know? Most people leave money on the table.",
 *   "mainPoints": ["Dividend investing", "Rental income", "Digital products", "Affiliate marketing"],
 *   "cta": "Link in bio to get started",
 *   "duration": 60,
 *   "hashtags": ["passiveincome", "investing"]
 * }
 *
 * # Generate batch of reels
 * POST /api/automation/instagram/batch
 * {
 *   "scripts": [{...}, {...}],
 *   "parallel": true,
 *   "scheduleTimeOffset": 86400000
 * }
 *
 * # Get reel status
 * GET /api/automation/instagram/status?reelId=reel-1234-abcd
 *
 * # Get metrics
 * GET /api/automation/instagram/metrics?reelId=reel-1234-abcd
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  generateAndPostReel,
  generateAndPostReelsBatch,
  getReelStatus,
  getReelMetrics,
  getAllReelStatuses,
  updateReelMetrics,
  ReelScript,
  InstagramReelMetadata,
} from '@/app/lib/automation/instagram';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface GenerateRequest {
  title: string;
  hook: string;
  mainPoints: string[];
  cta: string;
  duration?: number;
  voicePrompt?: string;
  backgroundMusic?: string;
  textOverlays?: string[];
  hashtags?: string[];
  contentTopic?: string;
  targetAudience?: string;
  affiliateLinks?: Record<string, string>;
  scheduleTime?: string;
  caption?: string;
}

interface BatchRequest {
  scripts: GenerateRequest[];
  parallel?: boolean;
  scheduleTimeOffset?: number;
  retries?: number;
}

interface APIResponse<T = unknown> {
  success: boolean;
  requestId?: string;
  data?: T;
  error?: string;
  timestamp?: string;
}

// ============================================================================
// AUTHENTICATION
// ============================================================================

function verifyAuth(request: NextRequest): boolean {
  const token = process.env.AUTOMATION_API_TOKEN;
  if (!token) {
    return true;
  }

  const authHeader = request.headers.get('Authorization');
  if (!authHeader) {
    return false;
  }

  const [scheme, credentials] = authHeader.split(' ');
  if (scheme !== 'Bearer') {
    return false;
  }

  return credentials === token;
}

// ============================================================================
// HANDLERS
// ============================================================================

/**
 * POST /api/automation/instagram/generate
 */
async function handleGenerate(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as GenerateRequest;

    // Validate required fields
    if (!body.title || !body.hook || !body.mainPoints || !body.cta) {
      return NextResponse.json(
        {
          success: false,
          error: 'Missing required fields: title, hook, mainPoints, cta',
        },
        { status: 400 }
      );
    }

    // Create script object
    const script: ReelScript = {
      title: body.title,
      hook: body.hook,
      mainPoints: body.mainPoints,
      cta: body.cta,
      duration: body.duration || 60,
      voicePrompt: body.voicePrompt,
      backgroundMusic: body.backgroundMusic,
      textOverlays: body.textOverlays,
      hashtags: body.hashtags,
      contentTopic: body.contentTopic,
      targetAudience: body.targetAudience,
      affiliateLinks: body.affiliateLinks,
    };

    // Generate and post reel
    const result = await generateAndPostReel(script, {
      scheduleTime: body.scheduleTime,
      caption: body.caption,
      retries: 3,
    });

    return NextResponse.json(
      {
        success: result.success,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: result.success ? 200 : 400 }
    );
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      {
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/automation/instagram/batch
 */
async function handleBatch(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as BatchRequest;

    if (!body.scripts || body.scripts.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: 'scripts array is required and must not be empty',
        },
        { status: 400 }
      );
    }

    // Convert requests to scripts
    const scripts: ReelScript[] = body.scripts.map((req) => ({
      title: req.title,
      hook: req.hook,
      mainPoints: req.mainPoints,
      cta: req.cta,
      duration: req.duration || 60,
      voicePrompt: req.voicePrompt,
      backgroundMusic: req.backgroundMusic,
      textOverlays: req.textOverlays,
      hashtags: req.hashtags,
      contentTopic: req.contentTopic,
      targetAudience: req.targetAudience,
      affiliateLinks: req.affiliateLinks,
    }));

    // Generate batch
    const result = await generateAndPostReelsBatch(scripts, {
      parallel: body.parallel ?? true,
      scheduleTimeOffset: body.scheduleTimeOffset ?? 86400000,
      retries: body.retries ?? 3,
    });

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      {
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/automation/instagram/status
 */
async function handleGetStatus(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
  try {
    const reelId = request.nextUrl.searchParams.get('reelId');

    if (!reelId) {
      // Return all statuses
      const allStatuses = await getAllReelStatuses();
      return NextResponse.json(
        {
          success: true,
          data: allStatuses,
          timestamp: new Date().toISOString(),
        },
        { status: 200 }
      );
    }

    // Return specific reel status
    const status = await getReelStatus(reelId);

    if (!status) {
      return NextResponse.json(
        {
          success: false,
          error: `Reel ${reelId} not found`,
        },
        { status: 404 }
      );
    }

    return NextResponse.json(
      {
        success: true,
        data: status,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      {
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/automation/instagram/metrics
 */
async function handleGetMetrics(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
  try {
    const reelId = request.nextUrl.searchParams.get('reelId');

    if (!reelId) {
      return NextResponse.json(
        {
          success: false,
          error: 'reelId query parameter is required',
        },
        { status: 400 }
      );
    }

    // Update metrics from Instagram
    const metadata = await updateReelMetrics(reelId);

    if (!metadata) {
      return NextResponse.json(
        {
          success: false,
          error: `Reel ${reelId} not found`,
        },
        { status: 404 }
      );
    }

    return NextResponse.json(
      {
        success: true,
        data: metadata.metrics || {},
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      {
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/automation/instagram/list
 */
async function handleList(
  _request: NextRequest
): Promise<NextResponse<APIResponse>> {
  try {
    const reels = await getAllReelStatuses();

    return NextResponse.json(
      {
        success: true,
        data: {
          total: reels.length,
          reels,
        },
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      {
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/automation/instagram/webhook
 */
async function handleWebhook(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
  try {
    const body = await request.json();

    // Handle various webhook events from video generation services
    // Synthesia, D-ID, Replicate, etc.
    const eventType = body.event || body.type || 'unknown';

    console.log(`Instagram reel webhook: ${eventType}`, body);

    return NextResponse.json(
      {
        success: true,
        data: { received: true },
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      {
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

// ============================================================================
// MAIN REQUEST HANDLER
// ============================================================================

export async function POST(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
  if (!verifyAuth(request)) {
    return NextResponse.json(
      {
        success: false,
        error: 'Unauthorized',
      },
      { status: 401 }
    );
  }

  const pathname = request.nextUrl.pathname;
  const requestId = `ig-api-${Date.now()}`;

  if (pathname.includes('/generate')) {
    return handleGenerate(request, requestId);
  } else if (pathname.includes('/batch')) {
    return handleBatch(request, requestId);
  } else if (pathname.includes('/webhook')) {
    return handleWebhook(request);
  } else {
    return NextResponse.json(
      {
        success: false,
        error: 'Unknown endpoint',
      },
      { status: 404 }
    );
  }
}

export async function GET(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
  if (!verifyAuth(request)) {
    return NextResponse.json(
      {
        success: false,
        error: 'Unauthorized',
      },
      { status: 401 }
    );
  }

  const pathname = request.nextUrl.pathname;

  if (pathname.includes('/status')) {
    return handleGetStatus(request);
  } else if (pathname.includes('/metrics')) {
    return handleGetMetrics(request);
  } else if (pathname.includes('/list')) {
    return handleList(request);
  } else {
    return NextResponse.json(
      {
        success: false,
        error: 'Unknown endpoint',
      },
      { status: 404 }
    );
  }
}
