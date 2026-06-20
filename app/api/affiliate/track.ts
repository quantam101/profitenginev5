/**
 * app/api/affiliate/track.ts
 *
 * Track affiliate link clicks for analytics and conversion funnel.
 * Records: partner, source, timestamp, user info
 *
 * POST /api/affiliate/track
 * Body: { partnerId: string, source: string, ... }
 *
 * Response: { success: true, tracked: true }
 */

import { NextRequest, NextResponse } from 'next/server';

interface AffiliateClickPayload {
  partnerId: string;
  source: string;
  userId?: string;
  userAgent?: string;
  referrer?: string;
}

/**
 * Log affiliate click to database (or file in development)
 *
 * In production, this writes to PostgreSQL/MongoDB
 * For now, logs to .runtime/audit/affiliate-clicks.jsonl
 */
async function logAffiliateClick(event: AffiliateClickPayload & { timestamp: string; sessionId?: string }) {
  // In production: write to database
  // const db = getDatabase();
  // await db.collection('affiliate_events').insertOne({
  //   type: 'click',
  //   partner: event.partnerId,
  //   source: event.source,
  //   timestamp: new Date(event.timestamp),
  //   sessionId: event.sessionId,
  //   userId: event.userId,
  //   userAgent: event.userAgent,
  //   referrer: event.referrer,
  // });

  // For now, log to console for audit trail
  console.log('[AFFILIATE_CLICK]', JSON.stringify(event));

  return { success: true };
}

/**
 * POST /api/affiliate/track
 *
 * Track an affiliate link click
 */
export async function POST(req: NextRequest) {
  try {
    // Parse request body
    const body = (await req.json()) as AffiliateClickPayload;

    const { partnerId, source, userId, userAgent } = body;

    // Validate required fields
    if (!partnerId || !source) {
      return NextResponse.json(
        {
          error: 'Missing required fields: partnerId, source',
          code: 'INVALID_REQUEST',
        },
        { status: 400 }
      );
    }

    // Validate partnerId format (alphanumeric + underscores)
    if (!/^[a-z0-9_]+$/.test(partnerId)) {
      return NextResponse.json(
        {
          error: 'Invalid partnerId format',
          code: 'INVALID_PARTNER_ID',
        },
        { status: 400 }
      );
    }

    // Extract request metadata
    const sessionId = req.cookies.get('__session')?.value;
    const ua = userAgent || req.headers.get('user-agent') || 'unknown';
    const referrer = body.referrer || req.headers.get('referer') || 'direct';

    // Build event payload
    const event: AffiliateClickPayload & { timestamp: string; sessionId?: string } = {
      partnerId,
      source,
      userId: userId || undefined,
      userAgent: ua,
      referrer,
      timestamp: new Date().toISOString(),
      sessionId: sessionId || undefined,
    };

    // Log to database/file
    await logAffiliateClick(event);

    // Return success response
    return NextResponse.json({
      success: true,
      tracked: true,
      partner: partnerId,
      source,
    });
  } catch (error) {
    // Log error for debugging
    console.error('[AFFILIATE_TRACK_ERROR]', error);

    // Return error response
    return NextResponse.json(
      {
        error: 'Failed to track click',
        code: 'TRACKING_FAILED',
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/affiliate/track
 *
 * Health check / stats endpoint
 */
export async function GET(req: NextRequest) {
  try {
    // Get query parameters
    const searchParams = req.nextUrl.searchParams;
    const days = parseInt(searchParams.get('days') || '7', 10);
    const partner = searchParams.get('partner');

    // Validate
    if (days < 1 || days > 365) {
      return NextResponse.json(
        { error: 'days parameter must be between 1 and 365' },
        { status: 400 }
      );
    }

    // In production, query database:
    // const events = await db.collection('affiliate_events')
    //   .find({
    //     timestamp: { $gte: new Date(Date.now() - days * 24 * 60 * 60 * 1000) },
    //     ...(partner ? { partner } : {}),
    //   })
    //   .toArray();

    // For now, return placeholder stats
    const stats = {
      period: `last_${days}_days`,
      totalClicks: 0,
      totalConversions: 0,
      totalRevenue: 0,
      byPartner: {},
      message: 'Tracking endpoint active. Connect database to see live stats.',
    };

    return NextResponse.json(stats);
  } catch (error) {
    console.error('[AFFILIATE_STATS_ERROR]', error);
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
