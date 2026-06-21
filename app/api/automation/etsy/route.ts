/**
 * API ENDPOINT: POST /api/automation/etsy
 *
 * Trigger Etsy/Printify automation from API request:
 * - Create new POD products from templates
 * - Sync inventory between Printify and Etsy
 * - Update prices based on cost + markup
 * - Track order status and fulfillment
 *
 * Requests:
 * ```json
 * // Create product
 * {
 *   "action": "create",
 *   "templates": [{ "name": "...", "printifyProductId": "16", ... }]
 * }
 *
 * // Sync inventory
 * {
 *   "action": "sync-inventory",
 *   "productMappings": [{ "printifyId": "...", "etsyId": ... }]
 * }
 *
 * // Update prices
 * {
 *   "action": "update-prices",
 *   "etsyListingId": 123,
 *   "markupPercent": 0.4
 * }
 *
 * // Track orders
 * {
 *   "action": "track-orders",
 *   "orderIds": ["order1", "order2"]
 * }
 * ```
 *
 * Response:
 * ```json
 * {
 *   "success": true,
 *   "action": "create",
 *   "results": [...],
 *   "timestamp": "2024-06-20T...",
 *   "duration": 1234
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  createPODProduct,
  syncInventory,
  updatePrices,
  trackOrder,
  batchTrackOrders,
  bulkCreateProducts,
  bulkSyncInventory,
  saveSyncReport,
  savePriceReport,
  loadProductMapping,
  ProductTemplate,
  PrintifyVariant,
} from '@/app/lib/automation/etsy';

// ═══════════════════════════════════════════════════════════════════════════════
// REQUEST/RESPONSE TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface CreateRequest {
  action: 'create';
  templates: ProductTemplate[];
  designUrls?: Record<string, string>;
}

interface SyncInventoryRequest {
  action: 'sync-inventory';
  productMappings: Array<{
    printifyId: string;
    etsyId: number;
    variantMapping: Record<
      string,
      { printifyId: string; etsyPropertyId: number }
    >;
  }>;
  saveReport?: boolean;
}

interface UpdatePricesRequest {
  action: 'update-prices';
  etsyListingId: number;
  printifyVariants: PrintifyVariant[];
  markupPercent?: number;
  saveReport?: boolean;
}

interface TrackOrdersRequest {
  action: 'track-orders';
  orderIds: string[];
}

type AutomationRequest =
  | CreateRequest
  | SyncInventoryRequest
  | UpdatePricesRequest
  | TrackOrdersRequest;

interface AutomationResponse {
  success: boolean;
  action: string;
  results?: unknown;
  error?: string;
  timestamp: string;
  duration: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// AUTHENTICATION & VALIDATION
// ═══════════════════════════════════════════════════════════════════════════════

function validateAuth(request: NextRequest): boolean {
  const authToken = request.headers.get('Authorization');
  const expectedToken = process.env.AUTOMATION_API_TOKEN;

  if (expectedToken && authToken !== `Bearer ${expectedToken}`) {
    return false;
  }

  return true;
}

function validateRequest(body: unknown): body is AutomationRequest {
  if (!body || typeof body !== 'object') {
    return false;
  }

  const obj = body as { action?: string };
  return ['create', 'sync-inventory', 'update-prices', 'track-orders'].includes(
    obj.action || ''
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// ACTION HANDLERS
// ═══════════════════════════════════════════════════════════════════════════════

async function handleCreate(req: CreateRequest): Promise<unknown> {
  console.log(`Creating ${req.templates.length} POD products...`);

  const designUrls = new Map(
    Object.entries(req.designUrls || {})
  );

  return bulkCreateProducts(req.templates, designUrls);
}

async function handleSyncInventory(req: SyncInventoryRequest): Promise<unknown> {
  console.log(`Syncing inventory for ${req.productMappings.length} products...`);

  const mappings = req.productMappings.map(m => ({
    printifyId: m.printifyId,
    etsyId: m.etsyId,
    variantMapping: new Map(Object.entries(m.variantMapping)),
  }));

  const reports = await bulkSyncInventory(mappings);

  if (req.saveReport) {
    for (const report of reports) {
      await saveSyncReport(report);
    }
  }

  return reports;
}

async function handleUpdatePrices(req: UpdatePricesRequest): Promise<unknown> {
  console.log(
    `Updating prices for Etsy listing ${req.etsyListingId} (${req.printifyVariants.length} variants)...`
  );

  const markup = req.markupPercent || parseFloat(process.env.POD_BASE_COST_MARKUP || '0.4');
  const report = await updatePrices(
    req.etsyListingId,
    req.printifyVariants,
    markup
  );

  if (req.saveReport) {
    await savePriceReport(report);
  }

  return report;
}

async function handleTrackOrders(req: TrackOrdersRequest): Promise<unknown> {
  console.log(`Tracking ${req.orderIds.length} orders...`);

  return batchTrackOrders(req.orderIds);
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN HANDLER
// ═══════════════════════════════════════════════════════════════════════════════

export async function POST(request: NextRequest): Promise<NextResponse<AutomationResponse>> {
  const startTime = Date.now();

  try {
    // Validate authentication
    if (!validateAuth(request)) {
      return NextResponse.json(
        {
          success: false,
          action: 'unknown',
          error: 'Unauthorized',
          timestamp: new Date().toISOString(),
          duration: 0,
        },
        { status: 401 }
      );
    }

    // Parse and validate request body
    const body = await request.json();

    if (!validateRequest(body)) {
      return NextResponse.json(
        {
          success: false,
          action: body?.action || 'unknown',
          error: 'Invalid request format. Action must be: create, sync-inventory, update-prices, or track-orders',
          timestamp: new Date().toISOString(),
          duration: Date.now() - startTime,
        },
        { status: 400 }
      );
    }

    // Route to action handler
    let results: unknown;

    switch (body.action) {
      case 'create':
        results = await handleCreate(body as CreateRequest);
        break;
      case 'sync-inventory':
        results = await handleSyncInventory(body as SyncInventoryRequest);
        break;
      case 'update-prices':
        results = await handleUpdatePrices(body as UpdatePricesRequest);
        break;
      case 'track-orders':
        results = await handleTrackOrders(body as TrackOrdersRequest);
        break;
      default:
        throw new Error(`Unknown action: ${body.action}`);
    }

    return NextResponse.json(
      {
        success: true,
        action: body.action,
        results,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Automation error:', error);

    return NextResponse.json(
      {
        success: false,
        action: 'unknown',
        error: (error as Error).message || 'Internal server error',
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      },
      { status: 500 }
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// GET ENDPOINT — Status & Configuration
// ═══════════════════════════════════════════════════════════════════════════════

interface StatusResponse {
  status: 'ok' | 'error';
  configured: {
    printify: boolean;
    etsy: boolean;
  };
  environment: Record<string, boolean>;
  timestamp: string;
}

export async function GET(request: NextRequest): Promise<NextResponse<StatusResponse>> {
  if (!validateAuth(request)) {
    return NextResponse.json(
      {
        status: 'error',
        configured: { printify: false, etsy: false },
        environment: {},
        timestamp: new Date().toISOString(),
      },
      { status: 401 }
    );
  }

  return NextResponse.json({
    status: 'ok',
    configured: {
      printify: !!(process.env.PRINTIFY_API_KEY && process.env.PRINTIFY_SHOP_ID),
      etsy: !!(process.env.ETSY_OAUTH_TOKEN && process.env.ETSY_SHOP_ID),
    },
    environment: {
      PRINTIFY_API_KEY: !!process.env.PRINTIFY_API_KEY,
      PRINTIFY_SHOP_ID: !!process.env.PRINTIFY_SHOP_ID,
      ETSY_OAUTH_TOKEN: !!process.env.ETSY_OAUTH_TOKEN,
      ETSY_SHOP_ID: !!process.env.ETSY_SHOP_ID,
      IMAGE_GENERATION_PROVIDER: !!process.env.IMAGE_GENERATION_PROVIDER,
      POD_BASE_COST_MARKUP: !!process.env.POD_BASE_COST_MARKUP,
    },
    timestamp: new Date().toISOString(),
  });
}
