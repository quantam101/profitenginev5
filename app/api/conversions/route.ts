/**
 * Conversions API
 * Tracks conversion events from landing page
 *
 * POST /api/conversions — Record conversion event
 * GET /api/conversions/metrics — Get metrics by section
 * GET /api/conversions/sections — Get all section metrics
 */

import { NextRequest, NextResponse } from 'next/server';

// In-memory event store (in production, use database)
// Format: sessionId -> Array<ConversionEvent>
const eventStore = new Map<string, any[]>();
const eventHistory: any[] = [];

// Keep last 10,000 events in memory
const MAX_EVENTS = 10000;

interface ConversionEvent {
  timestamp: string;
  section: string;
  action: string;
  sessionId?: string;
  metadata?: Record<string, any>;
}

export async function POST(request: NextRequest) {
  try {
    const event: ConversionEvent = await request.json();

    // Validate event
    if (!event.section || !event.action) {
      return NextResponse.json(
        { error: 'Missing required fields: section, action' },
        { status: 400 }
      );
    }

    // Store event
    const sessionId = event.sessionId || 'anonymous';

    if (!eventStore.has(sessionId)) {
      eventStore.set(sessionId, []);
    }

    eventStore.get(sessionId)!.push(event);
    eventHistory.push(event);

    // Trim history if too large
    if (eventHistory.length > MAX_EVENTS) {
      eventHistory.shift();
    }

    console.log(`[conversion] ${event.section}::${event.action}`, event.metadata);

    return NextResponse.json(
      { success: true, event },
      {
        headers: {
          'Cache-Control': 'no-store',
        },
      }
    );
  } catch (err) {
    console.error('Conversion tracking error:', err);

    return NextResponse.json(
      { error: 'Failed to record conversion' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const path = request.nextUrl.pathname;

  try {
    // GET /api/conversions/metrics?section=hero
    if (path.includes('/metrics')) {
      const section = searchParams.get('section');

      let events = eventHistory;
      if (section) {
        events = events.filter((e) => e.section === section);
      }

      // Calculate metrics by section
      const metricsMap = new Map<string, any>();

      for (const event of events) {
        if (!metricsMap.has(event.section)) {
          metricsMap.set(event.section, {
            section: event.section,
            clicks: 0,
            signups: 0,
            conversion_rate: 0,
          });
        }

        const metrics = metricsMap.get(event.section);

        if (event.action === 'cta_click' || event.action === 'link_click') {
          metrics.clicks++;
        } else if (event.action === 'signup') {
          metrics.signups++;
        }
      }

      // Calculate conversion rates
      const metrics = Array.from(metricsMap.values()).map((m) => ({
        ...m,
        conversion_rate:
          m.clicks > 0 ? ((m.signups / m.clicks) * 100).toFixed(2) : 0,
      }));

      return NextResponse.json(metrics, {
        headers: { 'Cache-Control': 'max-age=60' },
      });
    }

    // GET /api/conversions/sections
    if (path.includes('/sections')) {
      const sectionMetrics = new Map<string, any>();

      for (const event of eventHistory) {
        if (!sectionMetrics.has(event.section)) {
          sectionMetrics.set(event.section, {
            section: event.section,
            total_views: 0,
            total_clicks: 0,
            total_conversions: 0,
            click_through_rate: 0,
            conversion_rate: 0,
          });
        }

        const metrics = sectionMetrics.get(event.section);

        // Count event types
        if (event.action === 'metric_view' || event.action === 'performer_view') {
          metrics.total_views++;
        } else if (event.action === 'cta_click' || event.action === 'link_click') {
          metrics.total_clicks++;
        } else if (
          event.action === 'signup' ||
          event.action === 'tier_select'
        ) {
          metrics.total_conversions++;
        }
      }

      // Calculate rates
      const metrics = Array.from(sectionMetrics.values()).map((m) => ({
        ...m,
        click_through_rate:
          m.total_views > 0
            ? ((m.total_clicks / m.total_views) * 100).toFixed(2)
            : 0,
        conversion_rate:
          m.total_clicks > 0
            ? ((m.total_conversions / m.total_clicks) * 100).toFixed(2)
            : 0,
      }));

      return NextResponse.json(metrics, {
        headers: { 'Cache-Control': 'max-age=60' },
      });
    }

    // Default: return summary
    return NextResponse.json(
      {
        total_events: eventHistory.length,
        unique_sessions: eventStore.size,
        by_section: Array.from(
          new Map(eventHistory.map((e) => [e.section, true])).keys()
        ),
      },
      {
        headers: { 'Cache-Control': 'max-age=60' },
      }
    );
  } catch (err) {
    console.error('Conversion metrics error:', err);

    return NextResponse.json(
      { error: 'Failed to fetch metrics' },
      { status: 500 }
    );
  }
}

// Optional: DELETE endpoint to clear events
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const auth = searchParams.get('auth');

    // Simple auth check - use actual auth in production
    if (auth !== process.env.ADMIN_TOKEN) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    eventStore.clear();
    eventHistory.length = 0;

    return NextResponse.json({ success: true, message: 'Cleared all conversion events' });
  } catch (err) {
    console.error('Clear events error:', err);

    return NextResponse.json(
      { error: 'Failed to clear events' },
      { status: 500 }
    );
  }
}
