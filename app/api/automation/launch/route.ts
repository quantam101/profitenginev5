/**
 * API ENDPOINT: POST /api/automation/launch
 *
 * Trigger the full automation orchestration from API request
 * - Returns immediate response with run ID
 * - Executes async in background
 * - Results saved to .runtime/automation/launch-status.jsonl
 *
 * Request:
 * ```json
 * {
 *   "parallel": true,
 *   "skipTasks": ["carousel"],
 *   "webhookUrl": "https://your-endpoint.com/webhook"
 * }
 * ```
 *
 * Response:
 * ```json
 * {
 *   "success": true,
 *   "runId": "automation-1718894823456",
 *   "status": "initiated",
 *   "estimatedDuration": "180s",
 *   "tasks": ["gumroad", "carousel", "reel", "stories", "email"]
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';

// Dynamic import for server-side only
let orchestrateFullLaunch: (config?: Record<string, unknown>) => Promise<unknown>;
let getLatestAutomationStatus: () => Promise<unknown>;

/**
 * Initialize automation modules (lazy load to avoid client-side issues)
 */
async function initializeAutomation() {
  if (!orchestrateFullLaunch) {
    try {
      // These imports only work on server side
      const { orchestrateFullLaunch: ofl, getLatestAutomationStatus: glas } = await import(
        '@/app/lib/automation/orchestrate'
      );
      orchestrateFullLaunch = ofl;
      getLatestAutomationStatus = glas;
    } catch (error) {
      console.error('Failed to load automation modules:', error);
      throw new Error('Automation modules not available');
    }
  }
}

interface LaunchRequest {
  parallel?: boolean;
  skipTasks?: string[];
  webhookUrl?: string;
}

interface LaunchResponse {
  success: boolean;
  runId?: string;
  status?: string;
  estimatedDuration?: string;
  tasks?: string[];
  error?: string;
}

/**
 * POST /api/automation/launch — Trigger full automation
 */
export async function POST(request: NextRequest): Promise<NextResponse<LaunchResponse>> {
  try {
    // Verify request authentication (optional, but recommended for production)
    const authToken = request.headers.get('Authorization');
    const expectedToken = process.env.AUTOMATION_API_TOKEN;

    if (expectedToken && authToken !== `Bearer ${expectedToken}`) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Parse request body
    const body = (await request.json()) as LaunchRequest;
    const { parallel = true, skipTasks = [], webhookUrl } = body;

    // Initialize automation modules
    await initializeAutomation();

    // Generate run ID
    const runId = `automation-${Date.now()}`;

    // Prepare configuration
    const config = {
      parallel,
      skipTasks,
      runId,
    };

    // Start orchestration in background (don't await)
    if (typeof global !== 'undefined') {
      // Only on server
      setImmediate(async () => {
        try {
          const result = await orchestrateFullLaunch(config);

          // Notify via webhook if provided
          if (webhookUrl) {
            await fetch(webhookUrl, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                runId,
                result,
                timestamp: new Date().toISOString(),
              }),
            }).catch((error) => {
              console.error(`Webhook notification failed: ${error}`);
            });
          }
        } catch (error) {
          console.error(`Background automation failed: ${error}`);
        }
      });
    }

    return NextResponse.json({
      success: true,
      runId,
      status: 'initiated',
      estimatedDuration: parallel ? '180s' : '300s',
      tasks: ['gumroad', 'carousel', 'reel', 'stories', 'email'].filter(
        (t) => !skipTasks.includes(t)
      ),
    });
  } catch (error) {
    console.error('Launch request failed:', error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to start automation',
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/automation/launch — Get status of latest automation run
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    await initializeAutomation();

    const status = await getLatestAutomationStatus();

    return NextResponse.json({
      success: true,
      status,
    });
  } catch (error) {
    console.error('Status request failed:', error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get automation status',
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/automation/launch — CORS preflight
 */
export async function OPTIONS(): Promise<NextResponse> {
  return NextResponse.json(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
