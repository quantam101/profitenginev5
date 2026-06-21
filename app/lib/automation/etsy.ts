/**
 * ETSY + PRINTIFY AUTOMATION
 *
 * Automatically uploads Print-on-Demand (POD) products to Etsy via Printify API:
 * - Product creation from templates (t-shirts, hoodies, mugs, etc.)
 * - Inventory sync with Printify providers
 * - Dynamic price management with profit margins
 * - Order tracking and fulfillment status
 * - SKU generation and variant management
 *
 * Environment Requirements:
 * - PRINTIFY_API_KEY: Printify API token (from https://app.printify.com/dashboard)
 * - PRINTIFY_SHOP_ID: Your Printify shop ID
 * - ETSY_OAUTH_TOKEN: Etsy OAuth token (from https://www.etsy.com/developers)
 * - ETSY_SHOP_ID: Your Etsy shop ID
 * - ETSY_SELLER_KEY: Etsy developer key
 * - POD_BASE_COST_MARKUP: Markup percentage (0.3 = 30% margin, default: 0.4)
 * - IMAGE_GENERATION_PROVIDER: 'dalle' | 'replicate' (for design generation)
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES & INTERFACES
// ═══════════════════════════════════════════════════════════════════════════════

interface ProductTemplate {
  name: string;
  description: string;
  category: string;
  printifyProductId: string; // e.g., '16' for t-shirt
  designs: DesignVariant[];
  basePrice: number;
  tags: string[];
  shippingProfile?: string;
  materials?: string[];
}

interface DesignVariant {
  id: string;
  name: string;
  colors: string[];
  sizes: string[];
  imageUrl?: string;
  imagePrompt?: string;
  sku?: string;
}

interface PrintifyProduct {
  id: string;
  title: string;
  description: string;
  handle: string; // slug
  status: 'active' | 'draft' | 'archived';
  type: string;
  variants: PrintifyVariant[];
  tags: string[];
  images: Array<{ src: string; position: number }>;
  created_at: string;
  updated_at: string;
}

interface PrintifyVariant {
  id: string;
  title: string;
  sku: string;
  price: number;
  quantity: number;
  options: Array<{ name: string; value: string }>;
  image?: { src: string };
  status: 'active' | 'draft';
}

interface EtsyProduct {
  listing_id: number;
  user_id: number;
  shop_id: number;
  title: string;
  description: string;
  state: 'active' | 'inactive' | 'draft' | 'deactivated' | 'sold_out' | 'expired';
  creation_tsz: number;
  last_modified_tsz: number;
  ending_tsz?: number;
  original_creation_tsz: number;
  price: string;
  currency_code: string;
  quantity: number;
  tags: string[];
  category_id: number;
  taxonomy_id?: number;
  type: string;
  shipping_template_id?: number;
  processing_min?: number;
  processing_max?: number;
  materials?: string[];
  images?: Array<{ listing_image_id: number; hex_code?: string; url_570xN: string }>;
}

interface InventorySyncResult {
  success: boolean;
  productId?: string;
  variantId?: string;
  newQuantity?: number;
  previousQuantity?: number;
  printifyStatus?: string;
  error?: string;
}

interface PriceUpdateResult {
  success: boolean;
  productId?: string;
  variantId?: string;
  newPrice?: number;
  baseCost?: number;
  margin?: number;
  error?: string;
}

interface OrderTrackingResult {
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

interface SyncReport {
  timestamp: string;
  totalProducts: number;
  syncedVariants: number;
  failedVariants: number;
  totalQuantitySync: number;
  results: InventorySyncResult[];
  warnings: string[];
}

interface PriceUpdateReport {
  timestamp: string;
  totalVariants: number;
  updatedVariants: number;
  failedVariants: number;
  totalMarginAdjusted: number;
  results: PriceUpdateResult[];
  warnings: string[];
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRINTIFY API CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

class PrintifyClient {
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

  async createProduct(product: PrintifyProduct): Promise<string> {
    const result = await this.request('POST', '/products', product);
    return (result as { id: string }).id;
  }

  async getProduct(productId: string): Promise<PrintifyProduct> {
    return this.request('GET', `/products/${productId}`) as Promise<PrintifyProduct>;
  }

  async updateProduct(productId: string, updates: Partial<PrintifyProduct>): Promise<void> {
    await this.request('PUT', `/products/${productId}`, updates);
  }

  async getVariant(variantId: string): Promise<PrintifyVariant> {
    return this.request('GET', `/variants/${variantId}`) as Promise<PrintifyVariant>;
  }

  async updateVariant(variantId: string, updates: Partial<PrintifyVariant>): Promise<void> {
    await this.request('PUT', `/variants/${variantId}`, updates);
  }

  async getOrders(status?: string): Promise<unknown[]> {
    const query = status ? `?status=${status}` : '';
    return this.request('GET', `/orders${query}`) as Promise<unknown[]>;
  }

  async getOrder(orderId: string): Promise<unknown> {
    return this.request('GET', `/orders/${orderId}`);
  }

  async syncInventory(variantId: string, quantity: number): Promise<void> {
    await this.updateVariant(variantId, { quantity });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ETSY API CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

class EtsyClient {
  private accessToken: string;
  private shopId: string;
  private baseUrl = 'https://openapi.etsy.com/v3';

  constructor(accessToken?: string, shopId?: string) {
    this.accessToken = accessToken || process.env.ETSY_OAUTH_TOKEN || '';
    this.shopId = shopId || process.env.ETSY_SHOP_ID || '';

    if (!this.accessToken || !this.shopId) {
      throw new Error('ETSY_OAUTH_TOKEN and ETSY_SHOP_ID are required');
    }
  }

  async request(
    method: string,
    endpoint: string,
    body?: unknown
  ): Promise<unknown> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.accessToken}`,
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
        `Etsy API error [${response.status}]: ${error}`
      );
    }

    return response.json();
  }

  async createListing(listing: Partial<EtsyProduct>): Promise<number> {
    const result = await this.request('POST', `/application/shops/${this.shopId}/listings`, listing);
    return (result as { data: { listing_id: number } }).data.listing_id;
  }

  async updateListing(listingId: number, updates: Partial<EtsyProduct>): Promise<void> {
    await this.request('PATCH', `/application/shops/${this.shopId}/listings/${listingId}`, updates);
  }

  async getListing(listingId: number): Promise<EtsyProduct> {
    const result = await this.request(
      'GET',
      `/application/shops/${this.shopId}/listings/${listingId}`
    );
    return (result as { data: EtsyProduct }).data;
  }

  async uploadImage(
    listingId: number,
    imageUrl: string,
    rank: number = 1
  ): Promise<number> {
    // Etsy requires multipart/form-data for image uploads
    const formData = new FormData();
    const imageBlob = await fetch(imageUrl).then(r => r.blob());
    formData.append('image', imageBlob);
    formData.append('rank', rank.toString());

    const response = await fetch(
      `${this.baseUrl}/application/shops/${this.shopId}/listings/${listingId}/images`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.accessToken}`,
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Etsy image upload error [${response.status}]: ${error}`);
    }

    const result = await response.json();
    return (result as { data: { listing_image_id: number } }).data.listing_image_id;
  }

  async updateInventory(
    listingId: number,
    productionPartnerDeletes: Array<{ property_id: number; value_id: number }>,
    quantity: number
  ): Promise<void> {
    await this.request(
      'PUT',
      `/application/shops/${this.shopId}/listings/${listingId}/inventory`,
      {
        price_on_property: [200, 208], // common Etsy property IDs
        inventory: [
          {
            products: [{ product_id: 1, property_id: productionPartnerDeletes[0]?.property_id }],
            offerings: [{ quantity }],
          },
        ],
      }
    );
  }

  async getOrders(
    status?: 'open' | 'completed' | 'cancelled' | 'expired'
  ): Promise<unknown[]> {
    const query = status ? `?sort_on=created_tsz&status=${status}` : '';
    const result = await this.request(
      'GET',
      `/application/shops/${this.shopId}/orders${query}`
    );
    return (result as { data: unknown[] }).data || [];
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRODUCT CREATION & MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create a POD product on Printify and sync to Etsy
 */
export async function createPODProduct(
  template: ProductTemplate,
  designUrl?: string
): Promise<{ printifyId: string; etsyId: number }> {
  const printify = new PrintifyClient();
  const etsy = new EtsyClient();

  // Generate SKU from product name and variant
  const baseSku = template.name
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '-')
    .substring(0, 8);

  // Create on Printify
  const printifyProduct: PrintifyProduct = {
    id: '',
    title: template.name,
    description: template.description,
    handle: baseSku,
    status: 'active',
    type: template.printifyProductId,
    variants: template.designs.map((design, idx) => ({
      id: '',
      title: design.name,
      sku: `${baseSku}-${idx + 1}`,
      price: Math.round(template.basePrice * 100) / 100,
      quantity: 100, // default stock
      options: [
        { name: 'color', value: design.colors[0] || 'default' },
        { name: 'size', value: design.sizes[0] || 'medium' },
      ],
      status: 'active',
    })),
    tags: template.tags,
    images: designUrl
      ? [
          {
            src: designUrl,
            position: 1,
          },
        ]
      : [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const printifyId = await printify.createProduct(printifyProduct);
  console.log(`Created Printify product: ${printifyId}`);

  // Create on Etsy (link to Printify)
  const etsyListing: Partial<EtsyProduct> = {
    title: template.name,
    description: `${template.description}\n\nPrinted on demand by ${template.printifyProductId}.`,
    price: template.basePrice.toString(),
    quantity: 100,
    tags: template.tags,
    category_id: 2638, // default "unisex clothing" category
    materials: template.materials,
    shipping_template_id: 1, // requires existing template
    type: 'physical',
  };

  const etsyId = await etsy.createListing(etsyListing);
  console.log(`Created Etsy listing: ${etsyId}`);

  // Upload design image to Etsy
  if (designUrl) {
    try {
      await etsy.uploadImage(etsyId, designUrl, 1);
    } catch (error) {
      console.warn(`Failed to upload image to Etsy: ${(error as Error).message}`);
    }
  }

  return { printifyId, etsyId };
}

// ═══════════════════════════════════════════════════════════════════════════════
// INVENTORY SYNCHRONIZATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Sync inventory from Printify to Etsy
 * Printify is source of truth for available quantities
 */
export async function syncInventory(
  printifyProductId: string,
  etsyListingId: number,
  variantMapping: Map<string, { printifyId: string; etsyPropertyId: number }>
): Promise<SyncReport> {
  const printify = new PrintifyClient();
  const etsy = new EtsyClient();

  const report: SyncReport = {
    timestamp: new Date().toISOString(),
    totalProducts: 0,
    syncedVariants: 0,
    failedVariants: 0,
    totalQuantitySync: 0,
    results: [],
    warnings: [],
  };

  try {
    const product = await printify.getProduct(printifyProductId);
    report.totalProducts = 1;

    for (const variant of product.variants) {
      const mapping = variantMapping.get(variant.sku);
      if (!mapping) {
        report.warnings.push(`No Etsy mapping found for variant ${variant.sku}`);
        continue;
      }

      try {
        // Update Etsy inventory
        await etsy.updateInventory(
          etsyListingId,
          [{ property_id: mapping.etsyPropertyId, value_id: 1 }],
          variant.quantity
        );

        report.syncedVariants++;
        report.totalQuantitySync += variant.quantity;

        report.results.push({
          success: true,
          productId: printifyProductId,
          variantId: variant.id,
          newQuantity: variant.quantity,
          printifyStatus: variant.status,
        });
      } catch (error) {
        report.failedVariants++;
        report.results.push({
          success: false,
          productId: printifyProductId,
          variantId: variant.id,
          error: (error as Error).message,
        });
      }
    }
  } catch (error) {
    report.warnings.push(`Failed to fetch Printify product: ${(error as Error).message}`);
  }

  return report;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRICE MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Update prices on Etsy based on Printify base costs + markup
 */
export async function updatePrices(
  etsyListingId: number,
  printifyVariants: PrintifyVariant[],
  markupPercent: number = 0.4
): Promise<PriceUpdateReport> {
  const etsy = new EtsyClient();

  const report: PriceUpdateReport = {
    timestamp: new Date().toISOString(),
    totalVariants: printifyVariants.length,
    updatedVariants: 0,
    failedVariants: 0,
    totalMarginAdjusted: 0,
    results: [],
    warnings: [],
  };

  for (const variant of printifyVariants) {
    try {
      const baseCost = variant.price;
      const newPrice = Math.round(baseCost * (1 + markupPercent) * 100) / 100;
      const margin = newPrice - baseCost;

      await etsy.updateListing(etsyListingId, {
        price: newPrice.toString(),
      } as Partial<EtsyProduct>);

      report.updatedVariants++;
      report.totalMarginAdjusted += margin;

      report.results.push({
        success: true,
        variantId: variant.id,
        newPrice,
        baseCost,
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

  return report;
}

// ═══════════════════════════════════════════════════════════════════════════════
// ORDER TRACKING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get order status from Etsy and Printify
 */
export async function trackOrder(orderId: string): Promise<OrderTrackingResult> {
  const printify = new PrintifyClient();

  try {
    const order = await printify.getOrder(orderId);

    return {
      success: true,
      orderId,
      status: (order as { status: string }).status,
      trackingNumber: (order as { tracking_number?: string }).tracking_number,
      trackingUrl: (order as { tracking_url?: string }).tracking_url,
      carrier: (order as { carrier?: string }).carrier,
      estimatedDelivery: (order as { estimated_delivery?: string }).estimated_delivery,
      lastUpdate: new Date().toISOString(),
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
 * Batch fetch tracking for multiple orders
 */
export async function batchTrackOrders(
  orderIds: string[]
): Promise<OrderTrackingResult[]> {
  return Promise.all(orderIds.map(id => trackOrder(id)));
}

// ═══════════════════════════════════════════════════════════════════════════════
// BULK OPERATIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create multiple products from templates and sync to Etsy
 */
export async function bulkCreateProducts(
  templates: ProductTemplate[],
  designUrls: Map<string, string> = new Map()
): Promise<Array<{ template: ProductTemplate; printifyId: string; etsyId: number }>> {
  const results = [];

  for (const template of templates) {
    try {
      const designUrl = designUrls.get(template.name);
      const result = await createPODProduct(template, designUrl);
      results.push({
        template,
        printifyId: result.printifyId,
        etsyId: result.etsyId,
      });
      console.log(`✓ Created ${template.name} (Printify: ${result.printifyId}, Etsy: ${result.etsyId})`);
    } catch (error) {
      console.error(`✗ Failed to create ${template.name}: ${(error as Error).message}`);
    }
  }

  return results;
}

/**
 * Sync inventory across all linked products
 */
export async function bulkSyncInventory(
  productMappings: Array<{
    printifyId: string;
    etsyId: number;
    variantMapping: Map<string, { printifyId: string; etsyPropertyId: number }>;
  }>
): Promise<SyncReport[]> {
  const reports = [];

  for (const mapping of productMappings) {
    try {
      const report = await syncInventory(
        mapping.printifyId,
        mapping.etsyId,
        mapping.variantMapping
      );
      reports.push(report);
    } catch (error) {
      console.error(`Failed to sync ${mapping.printifyId}: ${(error as Error).message}`);
    }
  }

  return reports;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PERSISTENCE & REPORTING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Save sync report to file for monitoring
 */
export async function saveSyncReport(report: SyncReport, filename?: string): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';
  const reportFile = filename || path.join(runtimeDir, `etsy-sync-${Date.now()}.json`);

  // Ensure directory exists
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
  const reportFile = filename || path.join(runtimeDir, `etsy-price-${Date.now()}.json`);

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  await writeFile(reportFile, JSON.stringify(report, null, 2));
  console.log(`Price report saved to ${reportFile}`);
}

/**
 * Load product mapping from config file
 */
export async function loadProductMapping(
  configPath: string
): Promise<Array<{
  printifyId: string;
  etsyId: number;
  variantMapping: Map<string, { printifyId: string; etsyPropertyId: number }>;
}>> {
  try {
    const content = await readFile(configPath, 'utf-8');
    const config = JSON.parse(content);
    return config.products.map((p: unknown) => ({
      printifyId: (p as { printifyId: string }).printifyId,
      etsyId: (p as { etsyId: number }).etsyId,
      variantMapping: new Map(
        Object.entries((p as { variantMapping: Record<string, unknown> }).variantMapping)
      ),
    }));
  } catch (error) {
    console.error(`Failed to load config: ${(error as Error).message}`);
    return [];
  }
}

export {
  PrintifyClient,
  EtsyClient,
  ProductTemplate,
  DesignVariant,
  PrintifyProduct,
  PrintifyVariant,
  EtsyProduct,
  InventorySyncResult,
  PriceUpdateResult,
  OrderTrackingResult,
  SyncReport,
  PriceUpdateReport,
};
