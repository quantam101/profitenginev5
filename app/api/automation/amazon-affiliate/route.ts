/**
 * API ENDPOINT: POST /api/automation/amazon-affiliate
 *
 * Trigger Amazon Associates automation from API request:
 * - Search and create affiliate links
 * - Track clicks and conversions
 * - Generate commission reports
 * - Optimize link performance
 * - Bulk import products
 *
 * Requests:
 * ```json
 * // Search and create links
 * {
 *   "action": "create-links",
 *   "niche": "productivity",
 *   "keywords": ["project management", "collaboration"],
 *   "maxLinks": 5
 * }
 *
 * // Track click
 * {
 *   "action": "track-click",
 *   "linkId": "link-B0123456789-1234567890",
 *   "referer": "mysite.com"
 * }
 *
 * // Get commission report
 * {
 *   "action": "get-report",
 *   "startDate": "2024-06-01",
 *   "endDate": "2024-06-30",
 *   "links": [...]
 * }
 *
 * // Optimize links
 * {
 *   "action": "optimize-links",
 *   "links": [...]
 * }
 *
 * // Bulk import
 * {
 *   "action": "bulk-import",
 *   "products": [
 *     { "asin": "B0123456789", "niche": "productivity" }
 *   ]
 * }
 * ```
 *
 * Response:
 * ```json
 * {
 *   "success": true,
 *   "action": "create-links",
 *   "results": [...],
 *   "timestamp": "2024-06-20T...",
 *   "duration": 1234
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  createAffiliateLink,
  generateNicheLinks,
  batchCreateLinks,
  trackClick,
  trackConversion,
  getCommissionReport,
  getLinkAnalytics,
  optimizeLink,
  bulkOptimizeLinks,
  saveLinks,
  saveCommissionReport,
  bulkImportProducts,
  exportLinks,
  Product,
  AffiliateLink,
  CommissionReport,
  LinkOptimizationResult,
} from '@/app/lib/automation/amazon-affiliate';

// ═══════════════════════════════════════════════════════════════════════════════
// REQUEST/RESPONSE TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface CreateLinksRequest {
  action: 'create-links';
  niche: string;
  keywords: string[];
  maxLinks?: number;
  tag?: string;
}

interface TrackClickRequest {
  action: 'track-click';
  linkId: string;
  referer?: string;
  userId?: string;
}

interface TrackConversionRequest {
  action: 'track-conversion';
  linkId: string;
  amount: number;
  userId?: string;
}

interface GetReportRequest {
  action: 'get-report';
  startDate: string;
  endDate: string;
  links?: AffiliateLink[];
  saveReport?: boolean;
}

interface OptimizeLinksRequest {
  action: 'optimize-links';
  links: AffiliateLink[];
  applyChanges?: boolean;
}

interface BulkImportRequest {
  action: 'bulk-import';
  products: Array<{ asin: string; niche: string; title?: string }>;
  tag?: string;
  saveLinks?: boolean;
}

interface ExportLinksRequest {
  action: 'export-links';
  links: AffiliateLink[];
  format: 'json' | 'csv' | 'html';
}

type RequestBody =
  | CreateLinksRequest
  | TrackClickRequest
  | TrackConversionRequest
  | GetReportRequest
  | OptimizeLinksRequest
  | BulkImportRequest
  | ExportLinksRequest;

// ═══════════════════════════════════════════════════════════════════════════════
// API HANDLER
// ═══════════════════════════════════════════════════════════════════════════════

export async function POST(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now();

  try {
    const body = (await request.json()) as RequestBody;
    const action = body.action;

    // Create affiliate links
    if (action === 'create-links') {
      const req = body as CreateLinksRequest;
      const links = await generateNicheLinks(
        req.niche,
        req.keywords,
        req.maxLinks || 5,
        req.tag
      );

      return NextResponse.json({
        success: true,
        action: 'create-links',
        linkCount: links.length,
        links,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // Track click
    if (action === 'track-click') {
      const req = body as TrackClickRequest;
      const event = await trackClick(req.linkId, req.referer, req.userId);

      return NextResponse.json({
        success: true,
        action: 'track-click',
        event,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // Track conversion
    if (action === 'track-conversion') {
      const req = body as TrackConversionRequest;
      const event = await trackConversion(req.linkId, req.amount, req.userId);

      return NextResponse.json({
        success: true,
        action: 'track-conversion',
        event,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // Get commission report
    if (action === 'get-report') {
      const req = body as GetReportRequest;
      const report = await getCommissionReport(
        req.startDate,
        req.endDate,
        req.links || []
      );

      if (req.saveReport) {
        await saveCommissionReport(report);
      }

      return NextResponse.json({
        success: true,
        action: 'get-report',
        report,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // Optimize links
    if (action === 'optimize-links') {
      const req = body as OptimizeLinksRequest;
      const optimizations = await bulkOptimizeLinks(req.links);

      const appliedCount = optimizations.filter(
        o => o.appliedChanges.length > 0
      ).length;

      return NextResponse.json({
        success: true,
        action: 'optimize-links',
        optimizations,
        appliedCount,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // Bulk import products
    if (action === 'bulk-import') {
      const req = body as BulkImportRequest;
      const links = await bulkImportProducts(req.products, req.tag);

      if (req.saveLinks) {
        await saveLinks(links);
      }

      return NextResponse.json({
        success: true,
        action: 'bulk-import',
        importedCount: links.length,
        links,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // Export links
    if (action === 'export-links') {
      const req = body as ExportLinksRequest;
      const exported = await exportLinks(req.links, req.format);

      const contentType =
        req.format === 'json'
          ? 'application/json'
          : req.format === 'csv'
            ? 'text/csv'
            : 'text/html';

      return new NextResponse(exported, {
        headers: {
          'Content-Type': contentType,
          'Content-Disposition': `attachment; filename="affiliate-links.${req.format}"`,
        },
      });
    }

    // Unknown action
    return NextResponse.json(
      {
        success: false,
        error: `Unknown action: ${action}`,
        supportedActions: [
          'create-links',
          'track-click',
          'track-conversion',
          'get-report',
          'optimize-links',
          'bulk-import',
          'export-links',
        ],
      },
      { status: 400 }
    );
  } catch (error) {
    console.error('Amazon Affiliate API error:', error);

    return NextResponse.json(
      {
        success: false,
        error: (error as Error).message,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      },
      { status: 500 }
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// OPTIONS (CORS)
// ═══════════════════════════════════════════════════════════════════════════════

export async function OPTIONS(): Promise<NextResponse> {
  return NextResponse.json({}, { status: 200 });
}
