# Print-on-Demand (POD) Automation via Printify

Complete automation system for managing Print-on-Demand products, inventory, pricing, and order tracking through Printify API.

## Overview

The Printify integration provides:
- **Product Management**: Create products from 200+ blueprints (t-shirts, hoodies, mugs, etc.)
- **Inventory Sync**: Automatically sync quantities across variants and multiple products
- **Dynamic Pricing**: Automatic price calculations with configurable profit margins
- **Order Tracking**: Real-time order status and fulfillment tracking
- **Provider Discovery**: Access all available print providers (Printful, Gooten, Contrado, etc.)
- **Bulk Operations**: Batch create, price, and sync dozens of products simultaneously
- **Reporting**: Detailed sync and price update reports with audit trails

## Quick Start

### 1. Setup Environment Variables

```bash
# Required
PRINTIFY_API_KEY=your_api_key_here
PRINTIFY_SHOP_ID=your_shop_id_here

# Optional (with defaults)
POD_BASE_COST_MARKUP=0.4              # 40% profit margin
POD_DEFAULT_PROVIDER=1                # 1=Printful, see getPrintProviders()
RUNTIME_DATA_DIR=.runtime/automation  # Where to save reports
```

Get credentials from: https://app.printify.com/developers

### 2. Create a Product

```typescript
import { createProduct } from '@/app/lib/automation/printify';

const result = await createProduct(
  '16',                                    // Blueprint ID (t-shirt)
  'My Cool T-Shirt',
  'Premium quality print',
  'https://cdn.example.com/design.png',
  ['apparel', 'custom']
);

if (result.success) {
  console.log(`Product: ${result.productId}`);
  console.log(`Price: $${result.price} (Cost: $${result.cost}, Margin: $${result.margin})`);
}
```

### 3. Sync Inventory

```typescript
import { syncProductInventory } from '@/app/lib/automation/printify';

const report = await syncProductInventory('product-123', {
  'variant-black-s': 50,
  'variant-black-m': 75,
  'variant-white-s': 40,
});

console.log(`Synced ${report.syncedVariants} variants`);
```

### 4. Update Prices

```typescript
import { updateProductPrices } from '@/app/lib/automation/printify';

const report = await updateProductPrices('product-123', 0.45); // 45% margin

console.log(`Updated ${report.updatedVariants} variants`);
console.log(`Revenue impact: $${report.totalRevenueImpact}`);
```

### 5. Track Orders

```typescript
import { batchTrackOrders } from '@/app/lib/automation/printify';

const results = await batchTrackOrders(['order-1', 'order-2']);

results.forEach(r => {
  if (r.success) {
    console.log(`Order ${r.orderId}: ${r.status}`);
    if (r.trackingNumber) console.log(`  → ${r.trackingUrl}`);
  }
});
```

## API Routes

### POST /api/automation/printify

Main endpoint for all POD automation actions.

#### Create Product
```json
{
  "action": "create",
  "blueprintId": "16",
  "title": "T-Shirt Design",
  "description": "Description here",
  "imageUrl": "https://cdn.example.com/image.png",
  "tags": ["apparel"]
}
```

Response:
```json
{
  "success": true,
  "action": "create",
  "results": {
    "success": true,
    "productId": "prod_123",
    "title": "T-Shirt Design",
    "variantCount": 5,
    "sku": "t-shirt-des",
    "price": 29.99,
    "cost": 12.99,
    "margin": 17.00
  },
  "timestamp": "2024-06-20T...",
  "duration": 2345
}
```

#### Bulk Create
```json
{
  "action": "bulk-create",
  "products": [
    { "blueprintId": "16", "title": "Product 1", "description": "..." },
    { "blueprintId": "33", "title": "Product 2", "description": "..." }
  ]
}
```

#### Sync Inventory
```json
{
  "action": "sync-inventory",
  "productMappings": [
    {
      "productId": "prod-123",
      "quantityMap": {
        "var-1": 50,
        "var-2": 75
      }
    }
  ],
  "saveReport": true
}
```

#### Update Prices
```json
{
  "action": "update-prices",
  "productIds": ["prod-1", "prod-2"],
  "markupPercent": 0.4,
  "saveReport": true
}
```

#### Track Orders
```json
{
  "action": "track-orders",
  "orderIds": ["order-1", "order-2"]
}
```

#### Get Orders by Status
```json
{
  "action": "get-orders",
  "status": "pending"
}
```

#### Discover Blueprints
```json
{
  "action": "get-blueprints"
}
```

#### Search Blueprints
```json
{
  "action": "search-blueprints",
  "query": "t-shirt"
}
```

#### Get Providers
```json
{
  "action": "get-providers"
}
```

### GET /api/automation/printify

Check automation status and configuration.

Response:
```json
{
  "status": "ok",
  "configured": true,
  "apiKey": true,
  "shopId": true,
  "environment": {
    "PRINTIFY_API_KEY": true,
    "PRINTIFY_SHOP_ID": true,
    "POD_BASE_COST_MARKUP": true
  },
  "timestamp": "2024-06-20T..."
}
```

## Available Blueprints

Common blueprint IDs (use `getAvailableBlueprints()` for full list):

| ID | Product | Sizes | Colors |
|----|---------|-------|--------|
| 16 | T-Shirt (Unisex) | XS-3XL | 10+ |
| 26 | T-Shirt (Woman) | XS-2XL | 10+ |
| 33 | Hoodie | XS-3XL | 8+ |
| 52 | Mug (11oz) | One size | 5+ |
| 61 | Phone Case | Various | Various |
| 72 | Hat (Baseball) | One size | 6+ |

Use `searchBlueprints('hoodie')` to find products dynamically.

## Core Functions

### Product Management

```typescript
// Create single product
createProduct(
  blueprintId: string,
  title: string,
  description: string,
  imageUrl?: string,
  tags?: string[]
): Promise<ProductCreationResult>

// Create multiple products
bulkCreateProducts(
  products: Array<{
    blueprintId: string,
    title: string,
    description: string,
    imageUrl?: string,
    tags?: string[]
  }>
): Promise<ProductCreationResult[]>
```

### Inventory Management

```typescript
// Sync one product
syncProductInventory(
  productId: string,
  quantityMap: Record<string, number>
): Promise<SyncReport>

// Sync multiple products
bulkSyncInventory(
  productMappings: Array<{
    productId: string,
    quantityMap: Record<string, number>
  }>
): Promise<SyncReport[]>
```

### Pricing

```typescript
// Update prices for one product
updateProductPrices(
  productId: string,
  markupPercent?: number  // default: 0.4
): Promise<PriceUpdateReport>

// Update prices for multiple products
bulkUpdatePrices(
  productIds: string[],
  markupPercent?: number
): Promise<PriceUpdateReport[]>
```

### Order Tracking

```typescript
// Get single order
trackOrder(orderId: string): Promise<OrderTrackingResult>

// Batch track orders
batchTrackOrders(orderIds: string[]): Promise<OrderTrackingResult[]>

// Get orders by status
getOrdersByStatus(
  status?: 'pending' | 'confirmed' | 'fulfilled' | 'failed' | 'canceled'
): Promise<PrintifyOrder[]>
```

### Discovery

```typescript
// Get all available blueprints
getAvailableBlueprints(): Promise<PrintifyBlueprint[]>

// Search blueprints
searchBlueprints(query: string): Promise<PrintifyBlueprint[]>

// Get print providers
getPrintProviders(): Promise<PrintifyProvider[]>

// Get automation status
getAutomationStatus(): PODAutomationStatus
```

### Reporting

```typescript
// Save sync report to file
saveSyncReport(report: SyncReport, filename?: string): Promise<void>

// Save price update report to file
savePriceReport(report: PriceUpdateReport, filename?: string): Promise<void>

// Load product config
loadProductsConfig(configPath: string): Promise<Array<{...}>>
```

## Examples

See `printify-examples.ts` for complete usage patterns:

- `exampleCreateProduct()` — Create single product
- `exampleBulkCreate()` — Create multiple products
- `exampleSyncInventory()` — Sync inventory
- `exampleUpdatePrices()` — Update prices
- `exampleTrackOrders()` — Track orders
- `exampleDiscoverBlueprints()` — Find available products
- `exampleGetProviders()` — List print providers
- `exampleProductLaunchWorkflow()` — Complete product launch
- `exampleOrderManagement()` — Monitor orders

## Testing

Run the test suite:

```bash
npm test -- printify-automation.test.ts
```

Test with real Printify API:

```bash
# Set real credentials
export PRINTIFY_API_KEY=your_key
export PRINTIFY_SHOP_ID=your_shop_id

# Run tests
npm test -- printify-automation.test.ts
```

## Dashboard Integration

The POD Card component displays:
- Products count + creation rate
- Orders in progress
- 30-day revenue
- Order fulfillment rate
- Last sync timestamp

Add to dashboard:
```typescript
import { PODCard } from '@/app/components/dashboard/PODCard';

export function Dashboard() {
  return <PODCard />;
}
```

## Error Handling

All functions return success/error results:

```typescript
const result = await createProduct(...);

if (result.success) {
  console.log(`Created: ${result.productId}`);
} else {
  console.error(`Failed: ${result.error}`);
  // Handle error appropriately
}
```

Reports include warnings:
```typescript
const report = await syncProductInventory(...);

if (report.warnings.length > 0) {
  console.warn('Warnings during sync:');
  report.warnings.forEach(w => console.warn(`  - ${w}`));
}
```

## Price Margin Calculation

Default formula (40% margin):
```
baseCost = 12.99        // From blueprint
markup = 0.4            // From POD_BASE_COST_MARKUP
salePrice = baseCost × (1 + markup)
salePrice = 12.99 × 1.4 = 18.19
margin = salePrice - baseCost = 5.20
```

## Troubleshooting

**"PRINTIFY_API_KEY and PRINTIFY_SHOP_ID are required"**
- Set environment variables before calling functions
- Check credentials at https://app.printify.com/developers

**"Printify API error [401]"**
- Invalid API key
- Regenerate at https://app.printify.com/developers

**"Printify API error [404]"**
- Invalid product/variant/order ID
- Verify IDs in Printify dashboard

**No blueprint colors/sizes**
- Blueprint may not exist or changed format
- Call `getAvailableBlueprints()` to verify current list

**Inventory sync shows warnings**
- Check variant ID mappings match product structure
- Verify variant exists before syncing

## Rate Limiting

Printify API limits:
- 60 requests/minute per API key
- Implement retry with exponential backoff
- Batch operations when possible

## Performance

- **Bulk operations** (5-10 products): ~5-10 seconds
- **Single product**: ~1-2 seconds
- **Inventory sync**: ~0.5 seconds per product
- **Price update**: ~0.3 seconds per product

## Future Enhancements

- [ ] Webhook support for order status updates
- [ ] Machine learning pricing optimization
- [ ] Automated inventory rebalancing
- [ ] Multi-currency support
- [ ] Print provider comparison/optimization
- [ ] Customer review aggregation
- [ ] A/B testing framework for designs
- [ ] Integration with marketplace APIs (Etsy, eBay, Amazon)

## License

Part of ProfitEngine v5 — Internal use only

## Support

For issues or questions:
1. Check `PRINTIFY_README.md` (this file)
2. Review `printify-examples.ts` for usage patterns
3. Check test suite: `tests/printify-automation.test.ts`
4. Visit https://app.printify.com/api/docs
