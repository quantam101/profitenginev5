/**
 * ETSY + PRINTIFY AUTOMATION EXAMPLES
 *
 * Complete usage examples for the Etsy Shop automation module
 * demonstrating all major features and integration patterns.
 */

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
  ProductTemplate,
  SyncReport,
} from './etsy';

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 1: Create a Single POD Product
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleCreateSingleProduct() {
  const template: ProductTemplate = {
    name: 'Classic Black T-Shirt',
    description: 'Premium 100% cotton t-shirt with custom print design',
    category: 'apparel',
    printifyProductId: '16', // Printify t-shirt ID
    designs: [
      {
        id: 'design-front',
        name: 'Front Print Design',
        colors: ['white', 'black', 'navy'],
        sizes: ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        imageUrl: 'https://example.com/designs/front-print.png',
        sku: 'TSHIRT-BLACK-001',
      },
    ],
    basePrice: 24.99,
    tags: ['apparel', 't-shirt', 'custom', 'unisex'],
    materials: ['100% Cotton', 'Heavyweight'],
    shippingProfile: 'standard-domestic',
  };

  try {
    const result = await createPODProduct(
      template,
      'https://example.com/designs/front-print.png'
    );

    console.log(
      `Created POD product:\n` +
        `  Printify ID: ${result.printifyId}\n` +
        `  Etsy Listing ID: ${result.etsyId}`
    );

    return result;
  } catch (error) {
    console.error('Failed to create POD product:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 2: Bulk Create Multiple Products
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleBulkCreateProducts() {
  const templates: ProductTemplate[] = [
    {
      name: 'Classic T-Shirt',
      description: 'Premium quality t-shirt',
      category: 'apparel',
      printifyProductId: '16',
      designs: [
        {
          id: 'design-1',
          name: 'White',
          colors: ['white'],
          sizes: ['S', 'M', 'L', 'XL'],
        },
      ],
      basePrice: 19.99,
      tags: ['tee'],
    },
    {
      name: 'Cozy Hoodie',
      description: 'Comfortable pullover hoodie',
      category: 'apparel',
      printifyProductId: '18',
      designs: [
        {
          id: 'design-2',
          name: 'Black',
          colors: ['black'],
          sizes: ['S', 'M', 'L', 'XL', 'XXL'],
        },
      ],
      basePrice: 39.99,
      tags: ['hoodie'],
    },
    {
      name: 'Coffee Mug',
      description: 'Ceramic coffee mug with custom design',
      category: 'drinkware',
      printifyProductId: '50',
      designs: [
        {
          id: 'design-3',
          name: 'Standard White',
          colors: ['white'],
          sizes: ['11oz', '15oz'],
        },
      ],
      basePrice: 11.99,
      tags: ['mug', 'gift'],
    },
  ];

  const designUrls = new Map([
    ['Classic T-Shirt', 'https://example.com/tshirt-design.png'],
    ['Cozy Hoodie', 'https://example.com/hoodie-design.png'],
    ['Coffee Mug', 'https://example.com/mug-design.png'],
  ]);

  try {
    const results = await bulkCreateProducts(templates, designUrls);

    console.log(`Created ${results.length} products:`);
    results.forEach(r => {
      console.log(
        `  - ${r.template.name}: Printify ${r.printifyId}, Etsy ${r.etsyId}`
      );
    });

    return results;
  } catch (error) {
    console.error('Bulk creation failed:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 3: Sync Inventory from Printify to Etsy
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleSyncInventory() {
  const printifyProductId = 'prod_abc123';
  const etsyListingId = 987654321;

  // Map variant SKUs to Etsy property IDs
  const variantMapping = new Map([
    [
      'TSHIRT-WHITE-S',
      {
        printifyId: 'var_001',
        etsyPropertyId: 200, // Size property
      },
    ],
    [
      'TSHIRT-WHITE-M',
      {
        printifyId: 'var_002',
        etsyPropertyId: 200,
      },
    ],
    [
      'TSHIRT-WHITE-L',
      {
        printifyId: 'var_003',
        etsyPropertyId: 200,
      },
    ],
    [
      'TSHIRT-BLACK-S',
      {
        printifyId: 'var_004',
        etsyPropertyId: 200,
      },
    ],
  ]);

  try {
    const report = await syncInventory(
      printifyProductId,
      etsyListingId,
      variantMapping
    );

    console.log(`Inventory sync report:`);
    console.log(`  Timestamp: ${report.timestamp}`);
    console.log(`  Products synced: ${report.totalProducts}`);
    console.log(`  Variants synced: ${report.syncedVariants}`);
    console.log(`  Variants failed: ${report.failedVariants}`);
    console.log(`  Total quantity: ${report.totalQuantitySync} units`);

    if (report.warnings.length > 0) {
      console.warn(`Warnings:`);
      report.warnings.forEach(w => console.warn(`  - ${w}`));
    }

    return report;
  } catch (error) {
    console.error('Inventory sync failed:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 4: Bulk Sync Multiple Products
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleBulkSyncInventory() {
  const productMappings = [
    {
      printifyId: 'prod_tshirt_001',
      etsyId: 111111111,
      variantMapping: new Map([
        ['SKU-TSHIRT-S', { printifyId: 'var_1', etsyPropertyId: 200 }],
        ['SKU-TSHIRT-M', { printifyId: 'var_2', etsyPropertyId: 200 }],
      ]),
    },
    {
      printifyId: 'prod_hoodie_001',
      etsyId: 222222222,
      variantMapping: new Map([
        ['SKU-HOODIE-S', { printifyId: 'var_3', etsyPropertyId: 200 }],
        ['SKU-HOODIE-M', { printifyId: 'var_4', etsyPropertyId: 200 }],
      ]),
    },
  ];

  try {
    const reports = await bulkSyncInventory(productMappings);

    console.log(`Bulk sync completed: ${reports.length} products`);
    reports.forEach((report, idx) => {
      console.log(
        `  Product ${idx + 1}: ${report.syncedVariants}/${report.totalProducts} synced`
      );
    });

    // Optionally save reports to file
    for (const report of reports) {
      await saveSyncReport(report);
    }

    return reports;
  } catch (error) {
    console.error('Bulk sync failed:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 5: Update Prices with Markup
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleUpdatePrices() {
  const etsyListingId = 987654321;

  // Printify variant costs (from your Printify account)
  const variants = [
    {
      id: 'var_1',
      title: 'Small',
      sku: 'TSHIRT-S',
      price: 8.5,
      quantity: 50,
      options: [{ name: 'size', value: 'S' }],
      status: 'active' as const,
    },
    {
      id: 'var_2',
      title: 'Medium',
      sku: 'TSHIRT-M',
      price: 8.5,
      quantity: 75,
      options: [{ name: 'size', value: 'M' }],
      status: 'active' as const,
    },
    {
      id: 'var_3',
      title: 'Large',
      sku: 'TSHIRT-L',
      price: 9.0,
      quantity: 100,
      options: [{ name: 'size', value: 'L' }],
      status: 'active' as const,
    },
  ];

  // 40% markup (standard margin)
  const markupPercent = 0.4;

  try {
    const report = await updatePrices(
      etsyListingId,
      variants,
      markupPercent
    );

    console.log(`Price update report:`);
    console.log(`  Total variants: ${report.totalVariants}`);
    console.log(`  Updated: ${report.updatedVariants}`);
    console.log(`  Failed: ${report.failedVariants}`);
    console.log(`  Total margin adjusted: $${report.totalMarginAdjusted.toFixed(2)}`);

    report.results.forEach(r => {
      if (r.success) {
        console.log(
          `  ✓ ${r.variantId}: $${r.baseCost?.toFixed(2)} → $${r.newPrice?.toFixed(2)} (+$${r.margin?.toFixed(2)})`
        );
      }
    });

    // Save report
    await savePriceReport(report);

    return report;
  } catch (error) {
    console.error('Price update failed:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 6: Track Order Status
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleTrackOrder() {
  const orderId = 'order_abc123xyz';

  try {
    const result = await trackOrder(orderId);

    if (result.success) {
      console.log(`Order tracking for ${result.orderId}:`);
      console.log(`  Status: ${result.status}`);
      console.log(`  Tracking #: ${result.trackingNumber}`);
      console.log(`  Carrier: ${result.carrier}`);
      console.log(`  Est. Delivery: ${result.estimatedDelivery}`);
      console.log(`  Tracking URL: ${result.trackingUrl}`);
    } else {
      console.error(`Failed to track order: ${result.error}`);
    }

    return result;
  } catch (error) {
    console.error('Order tracking failed:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 7: Batch Track Multiple Orders
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleBatchTrackOrders() {
  const orderIds = [
    'order_001',
    'order_002',
    'order_003',
    'order_004',
    'order_005',
  ];

  try {
    const results = await batchTrackOrders(orderIds);

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`Batch tracking results:`);
    console.log(`  Successful: ${successful.length}/${results.length}`);
    console.log(`  Failed: ${failed.length}/${results.length}`);

    successful.forEach(r => {
      console.log(
        `  ✓ ${r.orderId}: ${r.status} | ${r.trackingNumber} (${r.carrier})`
      );
    });

    failed.forEach(r => {
      console.log(`  ✗ ${r.orderId}: ${r.error}`);
    });

    return results;
  } catch (error) {
    console.error('Batch tracking failed:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 8: Complete Workflow (Create → Sync → Track)
// ═══════════════════════════════════════════════════════════════════════════════

export async function exampleCompleteWorkflow() {
  console.log('=== STARTING COMPLETE ETSY POD WORKFLOW ===\n');

  try {
    // Step 1: Create product
    console.log('Step 1: Creating POD product...');
    const template: ProductTemplate = {
      name: 'Premium Unisex Hoodie',
      description: 'High-quality hoodie perfect for branding',
      category: 'apparel',
      printifyProductId: '18',
      designs: [
        {
          id: 'design-premium',
          name: 'Logo Print',
          colors: ['black', 'gray', 'navy'],
          sizes: ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
          imageUrl: 'https://example.com/logo.png',
        },
      ],
      basePrice: 44.99,
      tags: ['hoodie', 'premium', 'logo'],
      materials: ['80% Cotton', '20% Polyester'],
    };

    const createResult = await createPODProduct(
      template,
      'https://example.com/logo.png'
    );
    console.log(`  ✓ Created: Printify ${createResult.printifyId}, Etsy ${createResult.etsyId}\n`);

    // Step 2: Sync inventory
    console.log('Step 2: Syncing inventory...');
    const variantMapping = new Map([
      [
        'HOODIE-001',
        {
          printifyId: 'var_001',
          etsyPropertyId: 200,
        },
      ],
    ]);

    const syncResult = await syncInventory(
      createResult.printifyId,
      createResult.etsyId,
      variantMapping
    );
    console.log(`  ✓ Synced: ${syncResult.syncedVariants} variants\n`);

    // Step 3: Update prices
    console.log('Step 3: Updating prices...');
    const variants = [
      {
        id: 'var_001',
        title: 'Logo Hoodie',
        sku: 'HOODIE-001',
        price: 22.0,
        quantity: 100,
        options: [{ name: 'type', value: 'hoodie' }],
        status: 'active' as const,
      },
    ];

    const priceResult = await updatePrices(
      createResult.etsyId,
      variants,
      0.4
    );
    console.log(
      `  ✓ Updated: ${priceResult.updatedVariants} variants, $${priceResult.totalMarginAdjusted.toFixed(2)} margin\n`
    );

    // Step 4: Track orders (simulated)
    console.log('Step 4: Tracking orders...');
    const sampleOrderIds = ['order_new_001', 'order_new_002'];
    const trackResult = await batchTrackOrders(sampleOrderIds);
    const tracked = trackResult.filter(r => r.success).length;
    console.log(`  ✓ Tracked: ${tracked}/${trackResult.length} orders\n`);

    console.log('=== WORKFLOW COMPLETED SUCCESSFULLY ===');

    return {
      created: createResult,
      synced: syncResult,
      priced: priceResult,
      tracked: trackResult,
    };
  } catch (error) {
    console.error('Workflow failed:', (error as Error).message);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 9: Master Orchestrator Integration
// ═══════════════════════════════════════════════════════════════════════════════

export function getEtsyOrchestratorTask() {
  return {
    id: 'etsy-pod-sync',
    name: 'Etsy/Printify POD Automation',
    description: 'Sync inventory & track orders for print-on-demand products',
    type: 'etsy',
    enabled: !!(process.env.PRINTIFY_API_KEY && process.env.ETSY_OAUTH_TOKEN),
    priority: 'high',
    timeout: 240000, // 4 minutes
    retryMaxAttempts: 3,
    metadata: {
      action: 'sync-inventory',
      productMappings: [
        {
          printifyId: 'prod_123',
          etsyId: 987654321,
          variantMapping: {
            'SKU-001': { printifyId: 'var_001', etsyPropertyId: 200 },
            'SKU-002': { printifyId: 'var_002', etsyPropertyId: 200 },
          },
        },
      ],
    },
  };
}
