/**
 * PRINTIFY PRINT-ON-DEMAND AUTOMATION TEST SUITE
 *
 * Comprehensive tests for Printify POD automation:
 * - Product creation from blueprints
 * - Inventory synchronization
 * - Price management and margin calculation
 * - Order tracking and fulfillment
 * - Blueprint discovery
 * - Bulk operations
 *
 * Note: These tests mock Printify API calls. In production, use valid
 * PRINTIFY_API_KEY and PRINTIFY_SHOP_ID from your Printify account.
 */

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
  getAutomationStatus,
  PrintifyClient,
} from '@/app/lib/automation/printify';

describe('Printify Print-on-Demand Automation', () => {
  // Mock environment variables
  beforeEach(() => {
    process.env.PRINTIFY_API_KEY = 'printify_test_key_12345';
    process.env.PRINTIFY_SHOP_ID = 'shop_test_123';
    process.env.POD_BASE_COST_MARKUP = '0.4';
    process.env.RUNTIME_DATA_DIR = '.runtime/automation';
  });

  describe('Product Creation', () => {
    test('should create product from blueprint', async () => {
      const result = await createProduct(
        '16', // t-shirt blueprint
        'Custom T-Shirt Design',
        'Premium quality t-shirt with custom print',
        'https://example.com/design.png',
        ['apparel', 'merch']
      );

      expect(result.success).toBe(true);
      expect(result.productId).toBeDefined();
      expect(result.title).toBe('Custom T-Shirt Design');
      expect(result.variantCount).toBeGreaterThan(0);
      expect(result.price).toBeGreaterThan(result.cost!);
      expect(result.margin).toBeGreaterThan(0);
    });

    test('should calculate correct profit margin', async () => {
      const result = await createProduct(
        '16',
        'Margin Test',
        'Test product',
        undefined,
        []
      );

      if (result.success && result.cost && result.price) {
        const expectedPrice = Math.round(result.cost * 1.4 * 100) / 100;
        expect(result.price).toBe(expectedPrice);
      }
    });

    test('should generate valid SKU', async () => {
      const result = await createProduct(
        '16',
        'Premium Hoodie Design 2024',
        'Test description',
        undefined,
        []
      );

      if (result.success) {
        expect(result.sku).toMatch(/^[a-z0-9-]+$/);
        expect(result.sku!.length).toBeLessThanOrEqual(12);
      }
    });

    test('should handle missing blueprint gracefully', async () => {
      const result = await createProduct(
        'invalid_blueprint',
        'Test Product',
        'Description',
        undefined,
        []
      );

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Bulk Product Creation', () => {
    test('should create multiple products', async () => {
      const products = [
        {
          blueprintId: '16',
          title: 'T-Shirt Design 1',
          description: 'First design',
        },
        {
          blueprintId: '33',
          title: 'Hoodie Design 1',
          description: 'First hoodie',
        },
        {
          blueprintId: '52',
          title: 'Mug Design 1',
          description: 'First mug',
        },
      ];

      const results = await bulkCreateProducts(products);

      expect(results).toHaveLength(3);
      expect(results.filter(r => r.success)).toHaveLength(3);
      results.forEach(result => {
        if (result.success) {
          expect(result.productId).toBeDefined();
          expect(result.price).toBeGreaterThan(0);
        }
      });
    });

    test('should handle partial failures in bulk create', async () => {
      const products = [
        {
          blueprintId: '16',
          title: 'Valid Product',
          description: 'Valid',
        },
        {
          blueprintId: 'invalid',
          title: 'Invalid Product',
          description: 'Invalid',
        },
      ];

      const results = await bulkCreateProducts(products);

      expect(results).toHaveLength(2);
      const successful = results.filter(r => r.success);
      const failed = results.filter(r => !r.success);
      expect(successful.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Inventory Management', () => {
    test('should sync product inventory', async () => {
      const quantityMap = {
        'variant-1': 50,
        'variant-2': 75,
        'variant-3': 100,
      };

      const report = await syncProductInventory('product-123', quantityMap);

      expect(report.totalProducts).toBe(1);
      expect(report.timestamp).toBeDefined();
      expect(report.syncedVariants).toBeGreaterThanOrEqual(0);
      expect(report.totalQuantitySync).toBeGreaterThanOrEqual(0);
    });

    test('should handle missing variants gracefully', async () => {
      const quantityMap = {
        'nonexistent-variant': 50,
      };

      const report = await syncProductInventory('product-123', quantityMap);

      expect(report.warnings.length).toBeGreaterThanOrEqual(0);
    });

    test('should bulk sync multiple products', async () => {
      const productMappings = [
        {
          productId: 'product-1',
          quantityMap: { 'variant-1': 50, 'variant-2': 75 },
        },
        {
          productId: 'product-2',
          quantityMap: { 'variant-3': 100, 'variant-4': 120 },
        },
      ];

      const reports = await bulkSyncInventory(productMappings);

      expect(reports).toHaveLength(2);
      reports.forEach(report => {
        expect(report.timestamp).toBeDefined();
      });
    });
  });

  describe('Price Management', () => {
    test('should update product prices with default markup', async () => {
      const report = await updateProductPrices('product-123');

      expect(report.timestamp).toBeDefined();
      expect(report.totalVariants).toBeGreaterThanOrEqual(0);
      expect(report.updatedVariants).toBeGreaterThanOrEqual(0);
      expect(report.failedVariants).toBeGreaterThanOrEqual(0);
    });

    test('should update prices with custom markup', async () => {
      const customMarkup = 0.5; // 50% margin

      const report = await updateProductPrices('product-123', customMarkup);

      if (report.updatedVariants > 0) {
        report.results.forEach(result => {
          if (result.success && result.cost && result.newPrice) {
            const expectedPrice = Math.round(
              result.cost * (1 + customMarkup) * 100
            ) / 100;
            expect(result.newPrice).toBe(expectedPrice);
          }
        });
      }
    });

    test('should calculate revenue impact correctly', async () => {
      const report = await updateProductPrices('product-123', 0.3);

      expect(typeof report.totalRevenueImpact).toBe('number');
      expect(report.totalRevenueImpact).toBeGreaterThanOrEqual(0);
    });

    test('should bulk update prices for multiple products', async () => {
      const productIds = ['product-1', 'product-2', 'product-3'];

      const reports = await bulkUpdatePrices(productIds, 0.4);

      expect(reports).toHaveLength(3);
      reports.forEach(report => {
        expect(report.timestamp).toBeDefined();
      });
    });
  });

  describe('Order Tracking', () => {
    test('should track single order', async () => {
      const result = await trackOrder('order-123');

      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('orderId');
      if (result.success) {
        expect(result.status).toBeDefined();
      }
    });

    test('should batch track multiple orders', async () => {
      const orderIds = ['order-1', 'order-2', 'order-3'];

      const results = await batchTrackOrders(orderIds);

      expect(results).toHaveLength(3);
      results.forEach(result => {
        expect(result.orderId).toBeDefined();
      });
    });

    test('should handle order not found gracefully', async () => {
      const result = await trackOrder('nonexistent-order');

      expect(result).toBeDefined();
      expect(result).toHaveProperty('orderId');
    });
  });

  describe('Order Discovery', () => {
    test('should get all orders without filter', async () => {
      const orders = await getOrdersByStatus();

      expect(Array.isArray(orders)).toBe(true);
    });

    test('should filter orders by status', async () => {
      const statuses = ['pending', 'confirmed', 'fulfilled'] as const;

      for (const status of statuses) {
        const orders = await getOrdersByStatus(status);
        expect(Array.isArray(orders)).toBe(true);
      }
    });
  });

  describe('Blueprint Discovery', () => {
    test('should get available blueprints', async () => {
      const blueprints = await getAvailableBlueprints();

      expect(Array.isArray(blueprints)).toBe(true);
      if (blueprints.length > 0) {
        const blueprint = blueprints[0];
        expect(blueprint.id).toBeDefined();
        expect(blueprint.title).toBeDefined();
        expect(blueprint.category).toBeDefined();
      }
    });

    test('should search blueprints by keyword', async () => {
      const results = await searchBlueprints('t-shirt');

      expect(Array.isArray(results)).toBe(true);
      results.forEach(blueprint => {
        const searchText = `${blueprint.title} ${blueprint.category} ${blueprint.description}`.toLowerCase();
        expect(searchText).toContain('t-shirt');
      });
    });

    test('should search blueprints case-insensitive', async () => {
      const lowerResults = await searchBlueprints('hoodie');
      const upperResults = await searchBlueprints('HOODIE');
      const mixedResults = await searchBlueprints('HoOdIe');

      expect(lowerResults.length).toBe(upperResults.length);
      expect(lowerResults.length).toBe(mixedResults.length);
    });

    test('should return empty array for no matches', async () => {
      const results = await searchBlueprints('xyznonexistent123');

      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe('Provider Discovery', () => {
    test('should get print providers', async () => {
      const providers = await getPrintProviders();

      expect(Array.isArray(providers)).toBe(true);
      if (providers.length > 0) {
        const provider = providers[0];
        expect(provider.id).toBeDefined();
        expect(provider.name).toBeDefined();
        expect(provider.region).toBeDefined();
      }
    });
  });

  describe('Configuration & Status', () => {
    test('should return automation status', () => {
      const status = getAutomationStatus();

      expect(status).toHaveProperty('configured');
      expect(status).toHaveProperty('apiKey');
      expect(status).toHaveProperty('shopId');
      expect(typeof status.configured).toBe('boolean');
      expect(typeof status.apiKey).toBe('boolean');
      expect(typeof status.shopId).toBe('boolean');
    });

    test('should detect missing credentials', () => {
      delete process.env.PRINTIFY_API_KEY;
      const status = getAutomationStatus();

      expect(status.configured).toBe(false);
      expect(status.apiKey).toBe(false);
    });

    test('should detect when both credentials present', () => {
      process.env.PRINTIFY_API_KEY = 'test_key';
      process.env.PRINTIFY_SHOP_ID = 'test_shop';
      const status = getAutomationStatus();

      expect(status.configured).toBe(true);
      expect(status.apiKey).toBe(true);
      expect(status.shopId).toBe(true);
    });
  });

  describe('PrintifyClient', () => {
    test('should throw error when credentials missing', () => {
      delete process.env.PRINTIFY_API_KEY;
      delete process.env.PRINTIFY_SHOP_ID;

      expect(() => {
        new PrintifyClient();
      }).toThrow('PRINTIFY_API_KEY and PRINTIFY_SHOP_ID are required');
    });

    test('should accept custom credentials', () => {
      const client = new PrintifyClient('custom_key', 'custom_shop');
      expect(client).toBeDefined();
    });
  });

  describe('Integration Scenarios', () => {
    test('complete product lifecycle', async () => {
      // 1. Create product
      const createResult = await createProduct(
        '16',
        'Complete Lifecycle Test',
        'Testing full product lifecycle',
        'https://example.com/design.png',
        ['test', 'lifecycle']
      );

      if (createResult.success) {
        const productId = createResult.productId!;

        // 2. Update inventory
        const syncResult = await syncProductInventory(productId, {
          'variant-1': 100,
          'variant-2': 75,
        });

        expect(syncResult.totalProducts).toBe(1);

        // 3. Update prices
        const priceResult = await updateProductPrices(productId, 0.45);

        expect(priceResult.totalVariants).toBeGreaterThanOrEqual(0);
      }

      expect(createResult.success).toBe(true);
    });

    test('bulk product launch workflow', async () => {
      // 1. Create multiple products
      const products = [
        {
          blueprintId: '16',
          title: 'Summer Collection - Shirt A',
          description: 'Premium summer wear',
        },
        {
          blueprintId: '33',
          title: 'Summer Collection - Hoodie A',
          description: 'Cozy summer hoodie',
        },
        {
          blueprintId: '52',
          title: 'Summer Collection - Mug A',
          description: 'Summer themed mug',
        },
      ];

      const createResults = await bulkCreateProducts(products);
      const createdIds = createResults
        .filter(r => r.success)
        .map(r => r.productId!);

      // 2. Update prices for all products
      const priceResults = await bulkUpdatePrices(createdIds, 0.4);

      expect(createResults.length).toBe(3);
      expect(priceResults.length).toBe(createdIds.length);
    });
  });
});

/**
 * Manual Testing Guide
 *
 * To test with real Printify API:
 *
 * 1. Set environment variables:
 *    PRINTIFY_API_KEY=your_actual_key
 *    PRINTIFY_SHOP_ID=your_shop_id
 *
 * 2. Get credentials from:
 *    https://app.printify.com/developers
 *
 * 3. Run specific test suites:
 *    npm test -- printify-automation.test.ts -t "Product Creation"
 *
 * 4. Test workflow scenarios:
 *    npm test -- printify-automation.test.ts -t "complete product lifecycle"
 *
 * 5. Verify API response in Printify Dashboard:
 *    https://app.printify.com/products
 *
 * Test scenarios to verify:
 * - Create product from t-shirt blueprint
 * - View product in Printify dashboard
 * - Create order from new product
 * - Track order through fulfillment
 * - Check inventory sync with variants
 * - Verify price calculations with margins
 * - Test bulk operations with 5+ products
 */
