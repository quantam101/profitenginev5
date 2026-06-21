/**
 * ETSY/PRINTIFY AUTOMATION — DEMO & TESTING
 *
 * Example usage patterns for the Etsy/Printify automation system.
 * Run these examples to test different workflows.
 *
 * Usage:
 * ```bash
 * # Test product creation
 * ts-node examples/etsy-automation-demo.ts --test create
 *
 * # Test inventory sync
 * ts-node examples/etsy-automation-demo.ts --test sync
 *
 * # Test price updates
 * ts-node examples/etsy-automation-demo.ts --test price
 *
 * # Test order tracking
 * ts-node examples/etsy-automation-demo.ts --test orders
 * ```
 */

import {
  createPODProduct,
  syncInventory,
  updatePrices,
  trackOrder,
  bulkCreateProducts,
  ProductTemplate,
  PrintifyClient,
  EtsyClient,
} from '../app/lib/automation/etsy';
import { readFile } from 'fs/promises';

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO: CREATE PRODUCTS
// ═══════════════════════════════════════════════════════════════════════════════

async function demoCreateProduct() {
  console.log('\n📦 DEMO: Creating POD Product\n');

  const template: ProductTemplate = {
    name: 'Classic Trader T-Shirt',
    description: 'Premium 100% organic cotton t-shirt with trading graphics',
    category: 'apparel',
    printifyProductId: '16', // t-shirt
    basePrice: 24.99,
    designs: [
      {
        id: 'design-black',
        name: 'Black Shirt with Logo',
        colors: ['black'],
        sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'],
        imageUrl: 'https://via.placeholder.com/500x500?text=Trading+Logo',
        sku: 'trader-tshirt-black',
      },
    ],
    tags: ['t-shirt', 'trading', 'apparel'],
    materials: ['100% organic cotton'],
  };

  try {
    console.log('Creating product:', template.name);
    const result = await createPODProduct(template, template.designs[0].imageUrl);
    console.log('✓ Success!\n');
    console.log('Printify ID:', result.printifyId);
    console.log('Etsy ID:', result.etsyId);
    console.log('\nProduct URLs:');
    console.log(`  Printify: https://app.printify.com/products/${result.printifyId}`);
    console.log(`  Etsy: https://www.etsy.com/listing/${result.etsyId}`);
  } catch (error) {
    console.error('✗ Failed:', (error as Error).message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO: BULK CREATE PRODUCTS
// ═══════════════════════════════════════════════════════════════════════════════

async function demoBulkCreateProducts() {
  console.log('\n📦 DEMO: Bulk Create Products\n');

  const templates: ProductTemplate[] = [
    {
      name: 'Trading Blueprint T-Shirt',
      description: 'Show your trading strategy with this premium tee',
      category: 'apparel',
      printifyProductId: '16',
      basePrice: 24.99,
      designs: [
        {
          id: 'blueprint-black',
          name: 'Black Shirt',
          colors: ['black'],
          sizes: ['S', 'M', 'L', 'XL'],
          imageUrl: 'https://via.placeholder.com/500x500?text=Blueprint',
          sku: 'blueprint-black',
        },
      ],
      tags: ['t-shirt', 'trading', 'strategy'],
    },
    {
      name: 'Profit Engine Hoodie',
      description: 'Stay warm while trading with Profit Engine hoodie',
      category: 'apparel',
      printifyProductId: '22', // hoodie
      basePrice: 49.99,
      designs: [
        {
          id: 'engine-black',
          name: 'Black Hoodie',
          colors: ['black'],
          sizes: ['S', 'M', 'L', 'XL'],
          imageUrl: 'https://via.placeholder.com/500x500?text=Engine',
          sku: 'engine-hoodie',
        },
      ],
      tags: ['hoodie', 'profit', 'apparel'],
    },
    {
      name: 'Market Analysis Mug',
      description: 'Perfect for your morning coffee while analyzing markets',
      category: 'home',
      printifyProductId: '20', // mug
      basePrice: 12.99,
      designs: [
        {
          id: 'chart-mug',
          name: 'Chart Mug',
          colors: ['white'],
          sizes: ['11oz'],
          imageUrl: 'https://via.placeholder.com/300x400?text=Chart+Mug',
          sku: 'chart-mug-11oz',
        },
      ],
      tags: ['mug', 'trading', 'coffee'],
    },
  ];

  try {
    console.log(`Creating ${templates.length} products...`);
    const results = await bulkCreateProducts(templates);
    console.log(`\n✓ Successfully created ${results.length} products\n`);

    results.forEach((result, idx) => {
      console.log(`${idx + 1}. ${result.template.name}`);
      console.log(`   Printify: ${result.printifyId}`);
      console.log(`   Etsy: ${result.etsyId}`);
      console.log();
    });
  } catch (error) {
    console.error('✗ Failed:', (error as Error).message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO: SYNC INVENTORY
// ═══════════════════════════════════════════════════════════════════════════════

async function demoSyncInventory() {
  console.log('\n📊 DEMO: Sync Inventory\n');

  // Example mapping (replace with your actual IDs)
  const printifyProductId = 'YOUR_PRINTIFY_PRODUCT_ID';
  const etsyListingId = 123456789;

  const variantMapping = new Map([
    [
      'trader-tshirt-black',
      {
        printifyId: 'variant-123',
        etsyPropertyId: 200, // color property
      },
    ],
  ]);

  try {
    console.log(`Syncing inventory for Printify ${printifyProductId}...`);
    const report = await syncInventory(
      printifyProductId,
      etsyListingId,
      variantMapping
    );

    console.log('\n✓ Sync Complete\n');
    console.log(`Timestamp: ${report.timestamp}`);
    console.log(`Total Products: ${report.totalProducts}`);
    console.log(`Synced Variants: ${report.syncedVariants}`);
    console.log(`Failed Variants: ${report.failedVariants}`);
    console.log(`Total Quantity: ${report.totalQuantitySync}`);

    if (report.warnings.length > 0) {
      console.log('\n⚠️  Warnings:');
      report.warnings.forEach(w => console.log(`  - ${w}`));
    }

    console.log('\nResults:');
    report.results.forEach((result, idx) => {
      if (result.success) {
        console.log(
          `  ${idx + 1}. ✓ ${result.variantId}: ${result.newQuantity} units`
        );
      } else {
        console.log(`  ${idx + 1}. ✗ ${result.variantId}: ${result.error}`);
      }
    });
  } catch (error) {
    console.error('✗ Failed:', (error as Error).message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO: UPDATE PRICES
// ═══════════════════════════════════════════════════════════════════════════════

async function demoUpdatePrices() {
  console.log('\n💰 DEMO: Update Prices\n');

  const etsyListingId = 123456789;
  const printifyVariants = [
    {
      id: 'variant-1',
      title: 'Black/S',
      sku: 'trader-tshirt-black-s',
      price: 8.99, // base cost from Printify
      quantity: 100,
      options: [
        { name: 'color', value: 'black' },
        { name: 'size', value: 'S' },
      ],
      status: 'active' as const,
    },
    {
      id: 'variant-2',
      title: 'Black/M',
      sku: 'trader-tshirt-black-m',
      price: 8.99,
      quantity: 100,
      options: [
        { name: 'color', value: 'black' },
        { name: 'size', value: 'M' },
      ],
      status: 'active' as const,
    },
  ];
  const markupPercent = 0.4; // 40% markup

  try {
    console.log(`Updating prices for Etsy listing ${etsyListingId}`);
    console.log(`Markup: ${(markupPercent * 100).toFixed(0)}%\n`);

    const report = await updatePrices(
      etsyListingId,
      printifyVariants,
      markupPercent
    );

    console.log('✓ Price Update Complete\n');
    console.log(`Total Variants: ${report.totalVariants}`);
    console.log(`Updated: ${report.updatedVariants}`);
    console.log(`Failed: ${report.failedVariants}`);
    console.log(`Total Margin Adjusted: $${report.totalMarginAdjusted.toFixed(2)}\n`);

    console.log('Price Details:');
    report.results.forEach((result, idx) => {
      if (result.success) {
        console.log(
          `  ${idx + 1}. ${result.variantId}`
        );
        console.log(`     Base Cost: $${result.baseCost?.toFixed(2)}`);
        console.log(`     New Price: $${result.newPrice?.toFixed(2)}`);
        console.log(`     Margin: $${result.margin?.toFixed(2)}`);
      } else {
        console.log(`  ${idx + 1}. ✗ ${result.variantId}: ${result.error}`);
      }
    });
  } catch (error) {
    console.error('✗ Failed:', (error as Error).message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO: TRACK ORDERS
// ═══════════════════════════════════════════════════════════════════════════════

async function demoTrackOrders() {
  console.log('\n📦 DEMO: Track Orders\n');

  const orderIds = ['order-123', 'order-456', 'order-789'];

  try {
    console.log(`Tracking ${orderIds.length} orders...\n`);
    const results = await Promise.all(
      orderIds.map(id => trackOrder(id))
    );

    results.forEach((result, idx) => {
      console.log(`${idx + 1}. Order ${result.orderId}`);
      if (result.success) {
        console.log(`   Status: ${result.status}`);
        console.log(`   Tracking: ${result.trackingNumber}`);
        console.log(`   Carrier: ${result.carrier}`);
        console.log(`   Estimated Delivery: ${result.estimatedDelivery}`);
      } else {
        console.log(`   ✗ Error: ${result.error}`);
      }
      console.log();
    });
  } catch (error) {
    console.error('✗ Failed:', (error as Error).message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO: API REQUESTS
// ═══════════════════════════════════════════════════════════════════════════════

async function demoAPIRequests() {
  console.log('\n🌐 DEMO: API Requests\n');

  const baseUrl = process.env.BASE_URL || 'http://localhost:3000';
  const token = process.env.AUTOMATION_API_TOKEN || 'test-token';

  // 1. Health check
  console.log('1. Health Check\n');
  try {
    const response = await fetch(`${baseUrl}/api/automation/etsy`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const data = await response.json();
    console.log('✓ Status:', data.status);
    console.log('  Printify configured:', data.configured.printify);
    console.log('  Etsy configured:', data.configured.etsy);
  } catch (error) {
    console.error('✗ Request failed:', (error as Error).message);
  }

  // 2. Create product via API
  console.log('\n2. Create Product\n');
  try {
    const response = await fetch(`${baseUrl}/api/automation/etsy`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action: 'create',
        templates: [
          {
            name: 'API Test T-Shirt',
            description: 'Created via API request',
            category: 'apparel',
            printifyProductId: '16',
            basePrice: 24.99,
            designs: [
              {
                id: 'design-1',
                name: 'Black',
                colors: ['black'],
                sizes: ['S', 'M', 'L', 'XL'],
              },
            ],
            tags: ['test', 'api'],
          },
        ],
      }),
    });
    const data = await response.json();
    if (data.success) {
      console.log('✓ Product created');
      console.log('  Results:', JSON.stringify(data.results, null, 2));
    } else {
      console.log('✗ Error:', data.error);
    }
  } catch (error) {
    console.error('✗ Request failed:', (error as Error).message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function main() {
  const testType = process.argv[3] || 'demo';

  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║     ETSY/PRINTIFY AUTOMATION — DEMO & TESTING             ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  switch (testType) {
    case 'create':
      await demoCreateProduct();
      break;
    case 'bulk':
      await demoBulkCreateProducts();
      break;
    case 'sync':
      await demoSyncInventory();
      break;
    case 'price':
      await demoUpdatePrices();
      break;
    case 'orders':
      await demoTrackOrders();
      break;
    case 'api':
      await demoAPIRequests();
      break;
    case 'demo':
      console.log(`\nUsage:\n  npx ts-node examples/etsy-automation-demo.ts --test <type>\n`);
      console.log('Available tests:');
      console.log('  - create   : Create a single product');
      console.log('  - bulk     : Create multiple products');
      console.log('  - sync     : Sync inventory');
      console.log('  - price    : Update prices');
      console.log('  - orders   : Track orders');
      console.log('  - api      : Test API endpoints');
      console.log();
      break;
    default:
      console.error(`Unknown test type: ${testType}`);
      process.exit(1);
  }
}

main().catch(console.error);
