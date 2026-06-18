import { NextRequest, NextResponse } from 'next/server';

/**
 * Admin Action Executor
 * Handles all admin control panel actions with full audit logging
 * All actions require authentication and proper authorization
 */

const RUNTIME_API = process.env.RUNTIME_API_URL || 'http://runtime:8080';
const ADMIN_EMAIL = 'dispatch@alreadyherellc.com';

interface AdminAction {
  action: string;
  params: Record<string, any>;
  timestamp: string;
}

interface AuditLog {
  id: string;
  adminEmail: string;
  action: string;
  params: Record<string, any>;
  timestamp: string;
  ipAddress: string;
  result: 'success' | 'failed';
  errorMessage?: string;
}

// In-memory audit log (in production, persist to database)
const auditLogs: AuditLog[] = [];

async function executeRuntimeAction(
  action: string,
  params: Record<string, any>,
  adminEmail: string,
  ipAddress: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const endpointMap: Record<string, { path: string; method: string }> = {
      'toggle-system': { path: '/api/admin/toggle-system', method: 'POST' },
      'emergency-shutdown': { path: '/api/admin/emergency-shutdown', method: 'POST' },
      'toggle-risk-override': { path: '/api/admin/risk-override', method: 'POST' },
      'upgrade-tier': { path: '/api/admin/customer/upgrade-tier', method: 'POST' },
      'suspend-account': { path: '/api/admin/customer/suspend', method: 'POST' },
      'unsuspend-account': { path: '/api/admin/customer/unsuspend', method: 'POST' },
      'process-refund': { path: '/api/admin/customer/refund', method: 'POST' },
      'override-signal': { path: '/api/admin/signal-override', method: 'POST' },
    };

    const endpoint = endpointMap[action];
    if (!endpoint) {
      return { success: false, error: 'Unknown action' };
    }

    const response = await fetch(`${RUNTIME_API}${endpoint.path}`, {
      method: endpoint.method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
        'X-Admin-Email': adminEmail,
        'X-Admin-IP': ipAddress,
      },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(errorData.error || `Runtime API returned ${response.status}`);
    }

    const result = await response.json();

    // Log successful action
    logAction({
      adminEmail,
      action,
      params,
      ipAddress,
      result: 'success',
    });

    return { success: true };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    // Log failed action
    logAction({
      adminEmail,
      action,
      params,
      ipAddress,
      result: 'failed',
      errorMessage,
    });

    console.error(`[Admin] Action failed: ${action}`, error);
    return { success: false, error: errorMessage };
  }
}

function logAction(entry: {
  adminEmail: string;
  action: string;
  params: Record<string, any>;
  ipAddress: string;
  result: 'success' | 'failed';
  errorMessage?: string;
}) {
  const logEntry: AuditLog = {
    id: `log_${Date.now()}_${Math.random().toString(36).slice(2)}`,
    adminEmail: entry.adminEmail,
    action: entry.action,
    params: entry.params,
    timestamp: new Date().toISOString(),
    ipAddress: entry.ipAddress,
    result: entry.result,
    errorMessage: entry.errorMessage,
  };

  auditLogs.push(logEntry);

  // Keep last 1000 logs in memory
  if (auditLogs.length > 1000) {
    auditLogs.shift();
  }

  // Log to console (in production, send to logging service)
  const logMessage = `[Admin Audit] ${entry.adminEmail} @ ${entry.ipAddress} :: ${entry.action} :: ${entry.result}${
    entry.errorMessage ? ` :: ${entry.errorMessage}` : ''
  }`;

  if (entry.result === 'success') {
    console.log(logMessage);
  } else {
    console.error(logMessage);
  }
}

export async function POST(req: NextRequest) {
  try {
    // Verify admin access
    const userEmail = req.headers.get('x-user-email');
    if (userEmail !== ADMIN_EMAIL) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body: AdminAction = await req.json();
    const { action, params, timestamp } = body;

    if (!action) {
      return NextResponse.json(
        { error: 'Action required' },
        { status: 400 }
      );
    }

    const ipAddress = req.headers.get('x-forwarded-for') || req.headers.get('x-real-ip') || 'unknown';

    // Validate action timestamp (within 5 minutes)
    const actionTime = new Date(timestamp).getTime();
    const now = Date.now();
    if (Math.abs(now - actionTime) > 5 * 60 * 1000) {
      return NextResponse.json(
        { error: 'Request timestamp invalid (may be expired)' },
        { status: 400 }
      );
    }

    // Execute action
    const result = await executeRuntimeAction(action, params || {}, userEmail, ipAddress);

    if (!result.success) {
      return NextResponse.json(
        { error: result.error || 'Action failed' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: `Action ${action} executed successfully`,
    });
  } catch (error) {
    console.error('[Admin] Execute action error:', error);
    return NextResponse.json(
      { error: 'Failed to execute action' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/command/admin/execute-action (audit log retrieval)
 * Returns recent audit log entries
 */
export async function GET(req: NextRequest) {
  try {
    // Verify admin access
    const userEmail = req.headers.get('x-user-email');
    if (userEmail !== ADMIN_EMAIL) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const limit = parseInt(req.nextUrl.searchParams.get('limit') || '50', 10);

    return NextResponse.json({
      auditLogs: auditLogs.slice(-limit),
      total: auditLogs.length,
    });
  } catch (error) {
    console.error('[Admin] Audit log error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch audit log' },
      { status: 500 }
    );
  }
}
