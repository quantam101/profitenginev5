/**
 * PRINT-ON-DEMAND (POD) AUTOMATION
 *
 * Comprehensive Print-on-Demand automation for Printify integration:
 * - Product catalog management (t-shirts, hoodies, mugs, hats, etc.)
 * - Blueprint exploration and provider discovery
 * - Variant management (size, color, style options)
 * - Dynamic pricing with profit margin calculations
 * - Inventory tracking and stock synchronization
 * - Order status monitoring and fulfillment tracking
 * - Print provider management (Printful, Gooten, etc.)
 * - Bulk operations and batch processing
 * - Sales analytics and revenue tracking
 *
 * Environment Requirements:
 * - PRINTIFY_API_KEY: Printify API token (from https://app.printify.com/developers)
 * - PRINTIFY_SHOP_ID: Your Printify shop ID
 * - POD_BASE_COST_MARKUP: Markup percentage (0.3 = 30% margin, default: 0.4)
 * - POD_DEFAULT_PROVIDER: Default print provider ID (default: '1' for Printful)
 * - RUNTIME_DATA_DIR: Directory for storing reports (default: '.runtime/automation')
 */

import { readFile, writeFile, mkdir, appendFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES & INTERFACES
// ═══════════════════════════════════════════════════════════════════════════════

export interface PrintifyBlueprint {
  id: string;
  title: string;
  description: string;
  brand: string;
  model: string;
  image: string;
  category: string;
  colors: PrintifyColor[];
  sizes: PrintifySize[];
  printAreas: PrintifyPrintArea[];
}

export interface PrintifyColor {
  id: string;
  title: string;
  hex: string;
}

export interface PrintifySize {
  id: string;
  title: string;
  label: string;
}

export interface PrintifyPrintArea {
  id: string;
  title: string;
  width: number;
  height: number;
}

export interface PrintifyProduct {
  id: string;
  title: string;
  description: string;
  handle: string;
  status: 'active' | 'draft' | 'archived';
  blueprintId: string;
  variants: PrintifyVariant[];
  tags: string[];
  images: PrintifyImage[];
  createdAt: string;
  updatedAt: string;
}

export interface PrintifyVariant {
  id: string;
  title: string;
  sku: string;
  price: number;
  cost: number;
  available: boolean;
  quantity: number;
  options: Record<string, string>;
  image?: PrintifyImage;
  status: 'active' | 'archived';
}

export interface PrintifyImage {
  id: string;
  src: string;
  position: number;
  isDefault?: boolean;
}

export interface PrintifyOrder {
  id: string;
  externalOrderId?: string;
  status: 'pending' | 'confirmed' | 'failed' | 'canceled' | 'fulfilled';
  items: PrintifyOrderItem[];
  shipmentStatus?: string;
  trackingNumber?: string;
  trackingUrl?: string;
  carrier?: string;
  estimatedDelivery?: string;
  createdAt: string;
  updatedAt: string;
}

export interface PrintifyOrderItem {
  id: string;
  productId: string;
  variantId: string;
  quantity: number;
  price: number;
}

export interface PrintifyProvider {
  id: string;
  name: string;
  region: string;
  location: string;
  productsCount: number;
  rating: number;
}

export interface ProductCreationResult {
  success: boolean;
  productId?: string;
  title?: string;
  variantCount?: number;
  sku?: string;
  price?: number;
  cost?: number;
  margin?: number;
  error?: string;
}

export interface InventorySyncResult {
  success: boolean;
  productId?: string;
  variantId?: string;
  previousQuantity?: number;
  newQuantity?: number;
  syncedAt?: string;
  error?: string;
}

export interface PriceUpdateResult {
  success: boolean;
  variantId?: string;
  oldPrice?: number;
  newPrice?: number;
  cost?: number;
  margin?: number;
  error?: string;
}

export interface OrderTrackingResult {
  success: boolean;
  orderId?: string;
  status?: string;
  trackingNumber?: string;
  trackingUrl?: string;
  carrier?: string;
  estimatedDelivery?: string;
  lastUpdate?: string;
  error?: string;
}

export interface SyncReport {
  timestamp: string;
  totalProducts: number;
  syncedVariants: number;
  failedVariants: number;
  totalQuantitySync: number;
  results: InventorySyncResult[];
  warnings: string[];
}

export interface PriceUpdateReport {
  timestamp: string;
  totalVariants: number;
  updatedVariants: number;
  failedVariants: number;
  totalRevenueImpact: number;
  results: PriceUpdateResult[];
  warnings: string[];
}

export interface PODAutomationStatus {
  configured: boolean;
  apiKey: boolean;
  shopId: boolean;
  lastSync?: string;
  productsCount?: number;
  ordersInProgress?: number;
  totalRevenue?: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRINTIFY API CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

export class PrintifyClient {
  private apiKey: string;
  private shopId: string;
  private baseUrl = 'https://api.printify.com/v0';

  constructor(apiKey?: string, shopId?: string) {
    this.apiKey = apiKey || process.env.PRINTIFY_API_KEY || '';
    this.shopId = shopId || process.env.PRINTIFY_SHOP_ID || '';

    if (!this.apiKey || !this.shopId) {
      throw new Error('PRINTIFY_API_KEY and PRINTIFY_SHOP_ID are required');
    }
  }

  async request(
    method: string,
    endpoint: string,
    body?: unknown
  ): Promise<unknown> {
    const url = `${this.baseUrl}/shops/${this.shopId}${endpoint}`;
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
    };

    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(
        `Printify API error [${response.status}]: ${error}`
      );
    }

    return response.json();
  }

  // Blueprints API
  async getBlueprints(): Promise<PrintifyBlueprint[]> {
    const result = await this.request('GET', '/blueprints');
    return (result as { data: PrintifyBlueprint[] }).data || [];
  }

  async getBlueprint(blueprintId: string): Promise<PrintifyBlueprint> {
    return this.request('GET', `/blueprints/${blueprintId}`) as Promise<PrintifyBlueprint>;
  }

  // Products API
  async createProduct(product: Partial<PrintifyProduct>): Promise<string> {
    const result = await this.request('POST', '/products', product);
    return (result as { id: string }).id;
  }

  async getProduct(productId: string): Promise<PrintifyProduct> {
    return this.request('GET', `/products/${productId}`) as Promise<PrintifyProduct>;
  }

  async updateProduct(
    productId: string,
    updates: Partial<PrintifyProduct>
  ): Promise<void> {
    await this.request('PUT', `/products/${productId}`, updates);
  }

  async deleteProduct(productId: string): Promise<void> {
    await this.request('DELETE', `/products/${productId}`);
  }

  async getProducts(limit?: number): Promise<PrintifyProduct[]> {
    const query = limit ? `?limit=${limit}` : '';
    const result = await this.request('GET', `/products${query}`);
    return (result as { data: PrintifyProduct[] }).data || [];
  }

  // Variants API
  async getVariant(variantId: string): Promise<PrintifyVariant> {
    return this.request('GET', `/variants/${variantId}`) as Promise<PrintifyVariant>;
  }

  async updateVariant(
    variantId: string,
    updates: Partial<PrintifyVariant>
  ): Promise<void> {
    await this.request('PUT', `/variants/${variantId}`, updates);
  }

  // Orders API
  async getOrders(status?: string, limit?: number): Promise<PrintifyOrder[]> {
    let query = '';
    const params: string[] = [];
    if (status) params.push(`status=${status}`);
    if (limit) params.push(`limit=${limit}`);
    if (params.length > 0) query = '?' + params.join('&');

    const result = await this.request('GET', `/orders${query}`);
    return (result as { data: PrintifyOrder[] }).data || [];
  }

  async getOrder(orderId: string): Promise<PrintifyOrder> {
    return this.request('GET', `/orders/${orderId}`) as Promise<PrintifyOrder>;
  }

  async createOrder(order: Partial<PrintifyOrder>): Promise<string> {
    const result = await this.request('POST', '/orders', order);
    return (result as { id: string }).id;
  }

  // Providers API
  async getProviders(): Promise<PrintifyProvider[]> {
    const result = await this.request('GET', '/providers');
    return (result as { data: PrintifyProvider[] }).data || [];
  }

  // Image Upload
  async uploadImage(productId: string, imageUrl: string): Promise<string> {
    const result = await this.request('POST', `/products/${productId}/images`, {
      src: imageUrl,
      position: 1,
    });
    return (result as { id: string }).id;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRODUCT MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create a new POD product from a blueprint
 */
export async function createProduct(
  blueprintId: string,
  title: string,
  description: string,
  imageUrl?: string,
  tags: string[] = []
): Promise<ProductCreationResult> {
  const client = new PrintifyClient();
  const baseCostMarkup = parseFloat(process.env.POD_BASE_COST_MARKUP || '0.4');

  try {
    const blueprint = await client.getBlueprint(blueprintId);

    // Generate SKU from title
    const sku = title
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '-')
      .substring(0, 12);

    const product: Partial<PrintifyProduct> = {
      title,
      description,
      handle: sku,
      status: 'active',
      blueprintId,
      tags,
      variants: blueprint.colors.slice(0, 3).map((color, idx) => ({
        id: '',
        title: `${title} - ${color.title}`,
        sku: `${sku}-${color.id}`,
        price: 29.99, // default price
        cost: 12.99, // estimated base cost
        available: true,
        quantity: 100, // default stock
        options: { color: color.id },
        status: 'active',
      } as PrintifyVariant)),
      images: imageUrl
        ? [{ id: '', src: imageUrl, position: 1, isDefault: true }]
        : [],
    };

    const productId = await client.createProduct(product);

    // Upload image if provided
    if (imageUrl) {
      try {
        await client.uploadImage(productId, imageUrl);
      } catch (error) {
        console.warn(`Failed to upload image: ${(error as Error).message}`);
      }
    }

    const baseCost = 12.99;
    const salePrice = Math.round(baseCost * (1 + baseCostMarkup) * 100) / 100;
    const margin = salePrice - baseCost;

    return {
      success: true,
      productId,
      title,
      variantCount: product.variants!.length,
      sku,
      price: salePrice,
      cost: baseCost,
      margin,
    };
  } catch (error) {
    return {
      success: false,
      error: (error as Error).message,
    };
  }
}

/**
 * Create multiple products from templates
 */
export async function bulkCreateProducts(
  products: Array<{
    blueprintId: string;
    title: string;
    description: string;
    imageUrl?: string;
    tags?: string[];
  }>
): Promise<ProductCreationResult[]> {
  const results = [];

  for (const product of products) {
    const result = await createProduct(
      product.blueprintId,
      product.title,
      product.description,
      product.imageUrl,
      product.tags
    );
    results.push(result);

    if (result.success) {
      console.log(`✓ Created product: ${result.title}`);
    } else {
      console.error(`✗ Failed to create ${product.title}: ${result.error}`);
    }
  }

  return results;
}

// ═══════════════════════════════════════════════════════════════════════════════
// INVENTORY MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Sync inventory for a product's variants
 */
export async function syncProductInventory(
  productId: string,
  quantityMap: Record<string, number>
): Promise<SyncReport> {
  const client = new PrintifyClient();

  const report: SyncReport = {
    timestamp: new Date().toISOString(),
    totalProducts: 1,
    syncedVariants: 0,
    failedVariants: 0,
    totalQuantitySync: 0,
    results: [],
    warnings: [],
  };

  try {
    const product = await client.getProduct(productId);

    for (const variant of product.variants) {
      const newQuantity = quantityMap[variant.id];

      if (newQuantity === undefined) {
        report.warnings.push(`No quantity mapping for variant ${variant.id}`);
        continue;
      }

      try {
        const previousQuantity = variant.quantity;
        await client.updateVariant(variant.id, { quantity: newQuantity });

        report.syncedVariants++;
        report.totalQuantitySync += newQuantity;

        report.results.push({
          success: true,
          productId,
          variantId: variant.id,
          previousQuantity,
          newQuantity,
          syncedAt: new Date().toISOString(),
        });
      } catch (error) {
        report.failedVariants++;
        report.results.push({
          success: false,
          productId,
          variantId: variant.id,
          error: (error as Error).message,
        });
      }
    }
  } catch (error) {
    report.warnings.push(`Failed to fetch product: ${(error as Error).message}`);
  }

  return report;
}

/**
 * Sync inventory for multiple products
 */
export async function bulkSyncInventory(
  productMappings: Array<{
    productId: string;
    quantityMap: Record<string, number>;
  }>
): Promise<SyncReport[]> {
  const reports = [];

  for (const mapping of productMappings) {
    const report = await syncProductInventory(
      mapping.productId,
      mapping.quantityMap
    );
    reports.push(report);
  }

  return reports;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRICING MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Update prices for a product's variants based on cost + markup
 */
export async function updateProductPrices(
  productId: string,
  markupPercent?: number
): Promise<PriceUpdateReport> {
  const client = new PrintifyClient();
  const markup = markupPercent || parseFloat(process.env.POD_BASE_COST_MARKUP || '0.4');

  const report: PriceUpdateReport = {
    timestamp: new Date().toISOString(),
    totalVariants: 0,
    updatedVariants: 0,
    failedVariants: 0,
    totalRevenueImpact: 0,
    results: [],
    warnings: [],
  };

  try {
    const product = await client.getProduct(productId);
    report.totalVariants = product.variants.length;

    for (const variant of product.variants) {
      try {
        const cost = variant.cost || 12.99;
        const newPrice = Math.round(cost * (1 + markup) * 100) / 100;
        const oldPrice = variant.price;
        const margin = newPrice - cost;

        await client.updateVariant(variant.id, { price: newPrice });

        report.updatedVariants++;
        report.totalRevenueImpact += margin;

        report.results.push({
          success: true,
          variantId: variant.id,
          oldPrice,
          newPrice,
          cost,
          margin,
        });
      } catch (error) {
        report.failedVariants++;
        report.results.push({
          success: false,
          variantId: variant.id,
          error: (error as Error).message,
        });
      }
    }
  } catch (error) {
    report.warnings.push(`Failed to fetch product: ${(error as Error).message}`);
  }

  return report;
}

/**
 * Update prices for multiple products
 */
export async function bulkUpdatePrices(
  productIds: string[],
  markupPercent?: number
): Promise<PriceUpdateReport[]> {
  const reports = [];

  for (const productId of productIds) {
    const report = await updateProductPrices(productId, markupPercent);
    reports.push(report);
  }

  return reports;
}

// ═══════════════════════════════════════════════════════════════════════════════
// ORDER TRACKING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get order status and tracking information
 */
export async function trackOrder(orderId: string): Promise<OrderTrackingResult> {
  const client = new PrintifyClient();

  try {
    const order = await client.getOrder(orderId);

    return {
      success: true,
      orderId,
      status: order.status,
      trackingNumber: order.trackingNumber,
      trackingUrl: order.trackingUrl,
      carrier: order.carrier,
      estimatedDelivery: order.estimatedDelivery,
      lastUpdate: order.updatedAt,
    };
  } catch (error) {
    return {
      success: false,
      orderId,
      error: (error as Error).message,
    };
  }
}

/**
 * Batch track multiple orders
 */
export async function batchTrackOrders(orderIds: string[]): Promise<OrderTrackingResult[]> {
  return Promise.all(orderIds.map(id => trackOrder(id)));
}

/**
 * Get all orders with optional status filter
 */
export async function getOrdersByStatus(
  status?: 'pending' | 'confirmed' | 'failed' | 'canceled' | 'fulfilled'
): Promise<PrintifyOrder[]> {
  const client = new PrintifyClient();
  return client.getOrders(status);
}

// ═══════════════════════════════════════════════════════════════════════════════
// BLUEPRINT & PROVIDER DISCOVERY
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get available product blueprints (product templates)
 */
export async function getAvailableBlueprints(): Promise<PrintifyBlueprint[]> {
  const client = new PrintifyClient();
  return client.getBlueprints();
}

/**
 * Get print provider information
 */
export async function getPrintProviders(): Promise<PrintifyProvider[]> {
  const client = new PrintifyClient();
  return client.getProviders();
}

/**
 * Search blueprints by category or keyword
 */
export async function searchBlueprints(
  query: string
): Promise<PrintifyBlueprint[]> {
  const client = new PrintifyClient();
  const blueprints = await client.getBlueprints();

  const queryLower = query.toLowerCase();
  return blueprints.filter(
    b =>
      b.title.toLowerCase().includes(queryLower) ||
      b.category.toLowerCase().includes(queryLower) ||
      b.description.toLowerCase().includes(queryLower)
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// REPORTING & PERSISTENCE
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Save sync report to file
 */
export async function saveSyncReport(report: SyncReport, filename?: string): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';
  const reportFile = filename || path.join(runtimeDir, `printify-sync-${Date.now()}.json`);

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  await writeFile(reportFile, JSON.stringify(report, null, 2));
  console.log(`Sync report saved to ${reportFile}`);
}

/**
 * Save price update report to file
 */
export async function savePriceReport(
  report: PriceUpdateReport,
  filename?: string
): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';
  const reportFile = filename || path.join(runtimeDir, `printify-price-${Date.now()}.json`);

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  await writeFile(reportFile, JSON.stringify(report, null, 2));
  console.log(`Price report saved to ${reportFile}`);
}

/**
 * Get automation status and configuration
 */
export function getAutomationStatus(): PODAutomationStatus {
  return {
    configured:
      !!(process.env.PRINTIFY_API_KEY && process.env.PRINTIFY_SHOP_ID),
    apiKey: !!process.env.PRINTIFY_API_KEY,
    shopId: !!process.env.PRINTIFY_SHOP_ID,
  };
}

/**
 * Load products from local cache/config
 */
export async function loadProductsConfig(
  configPath: string
): Promise<Array<{ id: string; title: string; sku: string }>> {
  try {
    const content = await readFile(configPath, 'utf-8');
    const config = JSON.parse(content);
    return config.products || [];
  } catch (error) {
    console.error(`Failed to load config: ${(error as Error).message}`);
    return [];
  }
}

export {
  PrintifyProduct,
  PrintifyVariant,
  PrintifyBlueprint,
  PrintifyOrder,
  PrintifyProvider,
};
