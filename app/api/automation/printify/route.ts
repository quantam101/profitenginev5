/**
 * API ENDPOINT: POST /api/automation/printify
 *
 * Trigger Printify Print-on-Demand automation from API:
 * - Create new products from blueprints
 * - Sync inventory across variants
 * - Update prices based on cost + markup
 * - Track order status and fulfillment
 * - Discover available blueprints and providers
 *
 * Requests:
 * ```json
 * // Create product
 * {
 *   "action": "create",
 *   "blueprintId": "123",
 *   "title": "Product Name",
 *   "description": "Description",
 *   "imageUrl": "https://...",
 *   "tags": ["merch", "apparel"]
 * }
 *
 * // Create multiple products
 * {
 *   "action": "bulk-create",
 *   "products": [
 *     { "blueprintId": "123", "title": "...", ... }
 *   ]
 * }
 *
 * // Sync inventory
 * {
 *   "action": "sync-inventory",
 *   "productMappings": [
 *     { "productId": "...", "quantityMap": { "variant_id": 50 } }
 *   ]
 * }
 *
 * // Update prices
 * {
 *   "action": "update-prices",
 *   "productIds": ["product1", "product2"],
 *   "markupPercent": 0.4
 * }
 *
 * // Track orders
 * {
 *   "action": "track-orders",
 *   "orderIds": ["order1", "order2"]
 * }
 *
 * // Get order by status
 * {
 *   "action": "get-orders",
 *   "status": "pending"
 * }
 *
 * // Get blueprints
 * {
 *   "action": "get-blueprints"
 * }
 *
 * // Search blueprints
 * {
 *   "action": "search-blueprints",
 *   "query": "t-shirt"
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
  createProduct,
  bulkCreateProducts,
  syncProductInventory,
  bulkSyncInventory,
  updateProductPrices,
  bulkUpdatePrices,
  trackOrder,
  batchTrackOrders,
  getOrdersByStatus,
  getAvailableBlueprints,
  getPrintProviders,
  searchBlueprints,
  saveSyncReport,
  savePriceReport,
  getAutomationStatus,
  PrintifyBlueprint,
  PrintifyProvider,
  PrintifyOrder,
  ProductCreationResult,
  SyncReport,
  PriceUpdateReport,
  OrderTrackingResult,
} from '@/app/lib/automation/printify';

// ═══════════════════════════════════════════════════════════════════════════════
// REQUEST/RESPONSE TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface CreateRequest {
  action: 'create';
  blueprintId: string;
  title: string;
  description: string;
  imageUrl?: string;
  tags?: string[];
}

interface BulkCreateRequest {
  action: 'bulk-create';
  products: Array<{
    blueprintId: string;
    title: string;
    description: string;
    imageUrl?: string;
    tags?: string[];
  }>;
}

interface SyncInventoryRequest {
  action: 'sync-inventory';
  productMappings: Array<{
    productId: string;
    quantityMap: Record<string, number>;
  }>;
  saveReport?: boolean;
}

interface UpdatePricesRequest {
  action: 'update-prices';
  productIds: string[];
  markupPercent?: number;
  saveReport?: boolean;
}

interface TrackOrdersRequest {
  action: 'track-orders';
  orderIds: string[];
}

interface GetOrdersRequest {
  action: 'get-orders';
  status?: 'pending' | 'confirmed' | 'failed' | 'canceled' | 'fulfilled';
}

interface GetBlueprintsRequest {
  action: 'get-blueprints';
}

interface SearchBlueprintsRequest {
  action: 'search-blueprints';
  query: string;
}

interface GetProvidersRequest {
  action: 'get-providers';
}

type AutomationRequest =
  | CreateRequest
  | BulkCreateRequest
  | SyncInventoryRequest
  | UpdatePricesRequest
  | TrackOrdersRequest
  | GetOrdersRequest
  | GetBlueprintsRequest
  | SearchBlueprintsRequest
  | GetProvidersRequest;

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
  const validActions = [
    'create',
    'bulk-create',
    'sync-inventory',
    'update-prices',
    'track-orders',
    'get-orders',
    'get-blueprints',
    'search-blueprints',
    'get-providers',
  ];

  return validActions.includes(obj.action || '');
}

// ═══════════════════════════════════════════════════════════════════════════════
// ACTION HANDLERS
// ═══════════════════════════════════════════════════════════════════════════════

async function handleCreate(req: CreateRequest): Promise<unknown> {
  console.log(`Creating POD product: ${req.title}`);

  return createProduct(
    req.blueprintId,
    req.title,
    req.description,
    req.imageUrl,
    req.tags
  );
}

async function handleBulkCreate(req: BulkCreateRequest): Promise<unknown> {
  console.log(`Creating ${req.products.length} POD products`);

  return bulkCreateProducts(req.products);
}

async function handleSyncInventory(req: SyncInventoryRequest): Promise<unknown> {
  console.log(`Syncing inventory for ${req.productMappings.length} products`);

  const reports = await bulkSyncInventory(req.productMappings);

  if (req.saveReport) {
    for (const report of reports) {
      await saveSyncReport(report);
    }
  }

  return reports;
}

async function handleUpdatePrices(req: UpdatePricesRequest): Promise<unknown> {
  console.log(`Updating prices for ${req.productIds.length} products`);

  const reports = await bulkUpdatePrices(req.productIds, req.markupPercent);

  if (req.saveReport) {
    for (const report of reports) {
      await savePriceReport(report);
    }
  }

  return reports;
}

async function handleTrackOrders(req: TrackOrdersRequest): Promise<unknown> {
  console.log(`Tracking ${req.orderIds.length} orders`);

  return batchTrackOrders(req.orderIds);
}

async function handleGetOrders(req: GetOrdersRequest): Promise<unknown> {
  console.log(
    `Fetching orders with status: ${req.status || 'any'}`
  );

  return getOrdersByStatus(req.status);
}

async function handleGetBlueprints(): Promise<unknown> {
  console.log('Fetching available blueprints');

  return getAvailableBlueprints();
}

async function handleSearchBlueprints(req: SearchBlueprintsRequest): Promise<unknown> {
  console.log(`Searching blueprints: ${req.query}`);

  return searchBlueprints(req.query);
}

async function handleGetProviders(): Promise<unknown> {
  console.log('Fetching print providers');

  return getPrintProviders();
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
          error: 'Invalid request format',
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
      case 'bulk-create':
        results = await handleBulkCreate(body as BulkCreateRequest);
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
      case 'get-orders':
        results = await handleGetOrders(body as GetOrdersRequest);
        break;
      case 'get-blueprints':
        results = await handleGetBlueprints();
        break;
      case 'search-blueprints':
        results = await handleSearchBlueprints(body as SearchBlueprintsRequest);
        break;
      case 'get-providers':
        results = await handleGetProviders();
        break;
      default:
        throw new Error(`Unknown action: ${(body as { action?: string }).action}`);
    }

    return NextResponse.json(
      {
        success: true,
        action: (body as { action?: string }).action || 'unknown',
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
  configured: boolean;
  apiKey: boolean;
  shopId: boolean;
  environment: Record<string, boolean>;
  timestamp: string;
}

export async function GET(request: NextRequest): Promise<NextResponse<StatusResponse>> {
  if (!validateAuth(request)) {
    return NextResponse.json(
      {
        status: 'error',
        configured: false,
        apiKey: false,
        shopId: false,
        environment: {},
        timestamp: new Date().toISOString(),
      },
      { status: 401 }
    );
  }

  const automationStatus = getAutomationStatus();

  return NextResponse.json({
    status: automationStatus.configured ? 'ok' : 'error',
    configured: automationStatus.configured,
    apiKey: automationStatus.apiKey,
    shopId: automationStatus.shopId,
    environment: {
      PRINTIFY_API_KEY: automationStatus.apiKey,
      PRINTIFY_SHOP_ID: automationStatus.shopId,
      POD_BASE_COST_MARKUP: !!process.env.POD_BASE_COST_MARKUP,
      POD_DEFAULT_PROVIDER: !!process.env.POD_DEFAULT_PROVIDER,
    },
    timestamp: new Date().toISOString(),
  });
}
