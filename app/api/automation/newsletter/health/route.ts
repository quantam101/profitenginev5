/**
 * API ENDPOINT: /api/automation/newsletter/health
 *
 * Newsletter Automation Health Check
 * - GET: Fetch health status and enabled platforms
 */

import { NextRequest, NextResponse } from 'next/server';
import { newsletterEngine } from '@/app/lib/automation/newsletter';

export async function GET(
  request: NextRequest
): Promise<NextResponse> {
  try {
    const healthStatus = await newsletterEngine.getHealthStatus();

    return NextResponse.json({
      success: true,
      channel: 'email-newsletter',
      ...healthStatus,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Health check failed:', error);

    return NextResponse.json(
      {
        success: false,
        status: 'unavailable',
        error: error instanceof Error ? error.message : 'Health check failed',
      },
      { status: 500 }
    );
  }
}

export async function OPTIONS(): Promise<NextResponse> {
  return NextResponse.json(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
