/**
 * PRINTIFY INTEGRATION EXAMPLES
 *
 * Example usage patterns for Printify POD automation in the master orchestrator.
 * Shows how to integrate Print-on-Demand workflows with other automation modules.
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
} from './printify';

/**
 * Example 1: Create a single POD product
 */
export async function exampleCreateProduct() {
  console.log('Creating a new t-shirt product...');

  const result = await createProduct(
    '16', // t-shirt blueprint ID
    'Custom Design T-Shirt Summer 2024',
    'Premium quality t-shirt with eco-friendly print',
    'https://cdn.example.com/designs/summer-2024.png',
    ['apparel', 'summer', 'merch']
  );

  if (result.success) {
    console.log(`✓ Product created: ${result.productId}`);
    console.log(`  Title: ${result.title}`);
    console.log(`  Variants: ${result.variantCount}`);
    console.log(`  Price: $${result.price} (Cost: $${result.cost}, Margin: $${result.margin})`);
  } else {
    console.error(`✗ Failed to create product: ${result.error}`);
  }
}

/**
 * Example 2: Bulk create multiple products
 */
export async function exampleBulkCreate() {
  console.log('Creating multiple POD products...');

  const products = [
    {
      blueprintId: '16',
      title: 'Minimalist T-Shirt',
      description: 'Clean, modern design t-shirt',
      imageUrl: 'https://cdn.example.com/designs/minimal-tshirt.png',
      tags: ['apparel', 'minimalist'],
    },
    {
      blueprintId: '33',
      title: 'Premium Hoodie',
      description: 'Cozy, comfortable hoodie with custom print',
      imageUrl: 'https://cdn.example.com/designs/premium-hoodie.png',
      tags: ['apparel', 'hoodie', 'premium'],
    },
    {
      blueprintId: '52',
      title: 'Coffee Lover Mug',
      description: 'Perfect gift for coffee enthusiasts',
      imageUrl: 'https://cdn.example.com/designs/coffee-mug.png',
      tags: ['drinkware', 'gift'],
    },
  ];

  const results = await bulkCreateProducts(products);

  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);

  console.log(`✓ Created: ${successful.length}`);
  console.log(`✗ Failed: ${failed.length}`);

  successful.forEach(r => {
    console.log(`  - ${r.title} ($${r.price})`);
  });

  return results;
}

/**
 * Example 3: Sync inventory for a product
 */
export async function exampleSyncInventory() {
  console.log('Syncing product inventory...');

  const productId = 'pod-product-123';

  // Map variant IDs to quantities
  const quantityMap: Record<string, number> = {
    'variant-black-s': 50,
    'variant-black-m': 75,
    'variant-black-l': 100,
    'variant-white-s': 40,
    'variant-white-m': 60,
    'variant-white-l': 80,
  };

  const report = await syncProductInventory(productId, quantityMap);

  console.log(`Sync Report [${report.timestamp}]:`);
  console.log(`  Products: ${report.totalProducts}`);
  console.log(`  Synced: ${report.syncedVariants}`);
  console.log(`  Failed: ${report.failedVariants}`);
  console.log(`  Total Quantity: ${report.totalQuantitySync}`);

  if (report.warnings.length > 0) {
    console.log('  Warnings:');
    report.warnings.forEach(w => console.log(`    - ${w}`));
  }

  return report;
}

/**
 * Example 4: Update prices with margin calculation
 */
export async function exampleUpdatePrices() {
  console.log('Updating product prices...');

  const productIds = ['pod-product-1', 'pod-product-2', 'pod-product-3'];
  const markupPercent = 0.4; // 40% margin

  const reports = await bulkUpdatePrices(productIds, markupPercent);

  reports.forEach((report, idx) => {
    console.log(`Product ${idx + 1} [${report.timestamp}]:`);
    console.log(`  Updated: ${report.updatedVariants}`);
    console.log(`  Failed: ${report.failedVariants}`);
    console.log(`  Revenue Impact: $${report.totalRevenueImpact.toFixed(2)}`);
  });

  return reports;
}

/**
 * Example 5: Track orders and fulfillment
 */
export async function exampleTrackOrders() {
  console.log('Tracking order status...');

  const orderIds = ['order-1001', 'order-1002', 'order-1003'];

  const results = await batchTrackOrders(orderIds);

  results.forEach(result => {
    if (result.success) {
      console.log(`✓ Order ${result.orderId}:`);
      console.log(`  Status: ${result.status}`);
      if (result.trackingNumber) {
        console.log(`  Tracking: ${result.trackingNumber}`);
        console.log(`  Carrier: ${result.carrier}`);
      }
      if (result.estimatedDelivery) {
        console.log(`  Delivery: ${result.estimatedDelivery}`);
      }
    } else {
      console.log(`✗ Order ${result.orderId}: ${result.error}`);
    }
  });

  return results;
}

/**
 * Example 6: Discover available blueprints
 */
export async function exampleDiscoverBlueprints() {
  console.log('Discovering available product blueprints...');

  // Get all blueprints
  const allBlueprints = await getAvailableBlueprints();
  console.log(`Total blueprints available: ${allBlueprints.length}`);

  // Search for t-shirts
  const tshirts = await searchBlueprints('t-shirt');
  console.log(`\nT-shirt blueprints found: ${tshirts.length}`);
  tshirts.slice(0, 3).forEach(bp => {
    console.log(`  - ${bp.title} (${bp.brand})`);
    console.log(`    Colors: ${bp.colors.length}, Sizes: ${bp.sizes.length}`);
  });

  // Search for hoodies
  const hoodies = await searchBlueprints('hoodie');
  console.log(`\nHoodie blueprints found: ${hoodies.length}`);

  // Search for mugs
  const mugs = await searchBlueprints('mug');
  console.log(`Mug blueprints found: ${mugs.length}`);

  return { all: allBlueprints, tshirts, hoodies, mugs };
}

/**
 * Example 7: Get print providers
 */
export async function exampleGetProviders() {
  console.log('Getting print provider information...');

  const providers = await getPrintProviders();

  console.log(`Available providers: ${providers.length}`);
  providers.slice(0, 5).forEach(provider => {
    console.log(`  - ${provider.name} (${provider.region})`);
    console.log(`    Products: ${provider.productsCount}, Rating: ${provider.rating}/5`);
  });

  return providers;
}

/**
 * Example 8: Get orders by status
 */
export async function exampleGetOrdersByStatus() {
  console.log('Fetching orders by status...');

  // Get pending orders
  const pendingOrders = await getOrdersByStatus('pending');
  console.log(`Pending orders: ${pendingOrders.length}`);

  // Get confirmed orders
  const confirmedOrders = await getOrdersByStatus('confirmed');
  console.log(`Confirmed orders: ${confirmedOrders.length}`);

  // Get fulfilled orders
  const fulfilledOrders = await getOrdersByStatus('fulfilled');
  console.log(`Fulfilled orders: ${fulfilledOrders.length}`);

  return { pending: pendingOrders, confirmed: confirmedOrders, fulfilled: fulfilledOrders };
}

/**
 * Example 9: Complete product launch workflow
 */
export async function exampleProductLaunchWorkflow() {
  console.log('\n=== COMPLETE PRODUCT LAUNCH WORKFLOW ===\n');

  // Step 1: Discover blueprint
  console.log('Step 1: Discovering blueprint...');
  const blueprints = await searchBlueprints('t-shirt');
  const selectedBlueprint = blueprints[0];
  console.log(`Selected: ${selectedBlueprint.title}\n`);

  // Step 2: Create product
  console.log('Step 2: Creating product...');
  const createResult = await createProduct(
    selectedBlueprint.id,
    'Launch Product - Premium Tee',
    'Limited edition premium t-shirt',
    'https://cdn.example.com/designs/launch.png',
    ['launch', 'premium', 'limited']
  );

  if (!createResult.success) {
    console.error('Failed to create product');
    return;
  }

  const productId = createResult.productId!;
  console.log(`✓ Product created: ${productId}\n`);

  // Step 3: Set initial inventory
  console.log('Step 3: Setting initial inventory...');
  const syncResult = await syncProductInventory(productId, {
    'variant-0': 100,
    'variant-1': 100,
    'variant-2': 100,
  });
  console.log(`✓ Synced ${syncResult.syncedVariants} variants\n`);

  // Step 4: Set pricing
  console.log('Step 4: Setting prices with 45% margin...');
  const priceResult = await updateProductPrices(productId, 0.45);
  console.log(
    `✓ Updated ${priceResult.updatedVariants} variants, revenue impact: $${priceResult.totalRevenueImpact.toFixed(2)}\n`
  );

  // Step 5: Get status
  console.log('Step 5: Verifying configuration...');
  const status = getAutomationStatus();
  console.log(`✓ Automation configured: ${status.configured}`);
  console.log(`✓ API connected: ${status.apiKey && status.shopId}`);

  console.log('\n=== WORKFLOW COMPLETE ===\n');

  return {
    productId,
    createResult,
    syncResult,
    priceResult,
    status,
  };
}

/**
 * Example 10: Monitor and manage orders
 */
export async function exampleOrderManagement() {
  console.log('\n=== ORDER MANAGEMENT WORKFLOW ===\n');

  // Get pending orders
  console.log('Fetching pending orders...');
  const pendingOrders = await getOrdersByStatus('pending');
  console.log(`Found ${pendingOrders.length} pending orders\n`);

  if (pendingOrders.length > 0) {
    // Track first 3 orders
    const ordersToTrack = pendingOrders.slice(0, 3).map(o => o.id);
    console.log(`Tracking ${ordersToTrack.length} orders...\n`);

    const trackingResults = await batchTrackOrders(ordersToTrack);

    trackingResults.forEach(result => {
      if (result.success) {
        console.log(`✓ ${result.orderId}`);
        console.log(`  Status: ${result.status}`);
        if (result.trackingNumber) {
          console.log(`  Tracking: ${result.trackingNumber}`);
        }
      } else {
        console.log(`✗ ${result.orderId}: ${result.error}`);
      }
    });
  }

  // Get fulfilled orders count
  console.log('\nGetting fulfillment statistics...');
  const fulfilledOrders = await getOrdersByStatus('fulfilled');
  console.log(`Fulfilled orders: ${fulfilledOrders.length}`);

  console.log('\n=== ORDER MANAGEMENT COMPLETE ===\n');
}

/**
 * Example 11: Automation status check
 */
export async function exampleStatusCheck() {
  console.log('Checking automation status...');

  const status = getAutomationStatus();

  console.log(`Configured: ${status.configured}`);
  console.log(`API Key present: ${status.apiKey}`);
  console.log(`Shop ID present: ${status.shopId}`);

  if (status.configured) {
    console.log('✓ Ready to use');
  } else {
    console.log('✗ Missing configuration - set PRINTIFY_API_KEY and PRINTIFY_SHOP_ID');
  }

  return status;
}

/**
 * Run all examples
 */
export async function runAllExamples() {
  try {
    await exampleCreateProduct();
    console.log('\n---\n');

    await exampleBulkCreate();
    console.log('\n---\n');

    await exampleDiscoverBlueprints();
    console.log('\n---\n');

    await exampleGetProviders();
    console.log('\n---\n');

    await exampleProductLaunchWorkflow();
  } catch (error) {
    console.error('Example execution failed:', error);
  }
}
