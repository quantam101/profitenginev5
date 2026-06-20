/**
 * Gumroad Webhook Integration Tests
 *
 * Tests webhook payload parsing, transaction logging, and API integration.
 * Run with: npm test -- test_gumroad_webhook.ts
 */

describe('Gumroad Webhook Integration', () => {
  const WEBHOOK_URL = 'http://localhost:3000/api/webhooks/gumroad';

  describe('Webhook Handler', () => {
    it('should accept valid Gumroad sale payload', async () => {
      const payload = {
        product_id: 'prod_test_123',
        product_name: 'Trading Guide 2026',
        price: '29.99',
        purchase_email: 'trader@example.com',
        license_key: 'LICENSE_abc123',
        variant_title: 'PDF Bundle',
        timestamp: Math.floor(Date.now() / 1000),
        currency: 'usd',
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.amount_usd).toBe(29.99);
      expect(data.purchaser_email).toBe('trader@example.com');
      expect(data.product_name).toBe('Trading Guide 2026');
    });

    it('should normalize prices correctly', async () => {
      // Test with string price
      const payload = {
        product_id: 'prod_test_456',
        product_name: 'Ebook',
        price: '49.99',
        purchase_email: 'buyer@example.com',
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.amount_usd).toBe(49.99);
    });

    it('should handle missing optional fields', async () => {
      const payload = {
        product_id: 'prod_test_789',
        product_name: 'Basic Ebook',
        price: '19.99',
        purchase_email: 'user@example.com',
        // No license_key, variant_title, or timestamp
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.amount_usd).toBe(19.99);
    });

    it('should reject missing required fields', async () => {
      const payload = {
        product_id: 'prod_test_bad',
        // Missing product_name, price, purchase_email
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(400);
      const data = await response.json();
      expect(data.ok).toBe(false);
    });

    it('should provide health check on GET', async () => {
      const response = await fetch(WEBHOOK_URL, {
        method: 'GET',
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.service).toBe('Gumroad Webhook Handler');
      expect(data.version).toBe('2.0');
      expect(data.expected_fields).toContain('product_id');
      expect(data.expected_fields).toContain('price');
    });

    it('should log transactions to JSONL file', async () => {
      const payload = {
        product_id: 'prod_test_log',
        product_name: 'Test Product',
        price: '9.99',
        purchase_email: 'test@example.com',
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.logged).toBe(true);

      // Verify file was written
      const fs = await import('fs');
      const transactionLog = fs.readFileSync('.runtime/revenue/transactions.jsonl', 'utf8');
      expect(transactionLog).toContain('prod_test_log');
      expect(transactionLog).toContain('test@example.com');
    });

    it('should normalize email addresses to lowercase', async () => {
      const payload = {
        product_id: 'prod_email_test',
        product_name: 'Email Test',
        price: '14.99',
        purchase_email: 'TRADER@EXAMPLE.COM',
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.purchaser_email).toBe('trader@example.com');
    });

    it('should include transaction details in response', async () => {
      const payload = {
        product_id: 'prod_details_test',
        product_name: 'Details Test Product',
        price: '39.99',
        purchase_email: 'detail@example.com',
        license_key: 'LICENSE_test123',
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.transaction_id).toBeDefined();
      expect(data.transaction_id).toContain('gumroad_prod_details_test');
      expect(data.processing_time_ms).toBeDefined();
      expect(data.processing_time_ms).toBeGreaterThan(0);
      expect(data.processing_time_ms).toBeLessThan(5000);
    });
  });

  describe('Transaction Schema', () => {
    it('should match transaction log schema', async () => {
      const payload = {
        product_id: 'prod_schema_test',
        product_name: 'Schema Test',
        price: '24.99',
        purchase_email: 'schema@example.com',
        license_key: 'LICENSE_schema',
        variant_title: 'PDF',
      };

      await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const fs = await import('fs');
      const lines = fs
        .readFileSync('.runtime/revenue/transactions.jsonl', 'utf8')
        .split('\n')
        .filter((line) => line.trim());

      const lastLine = lines[lines.length - 1];
      const transaction = JSON.parse(lastLine);

      // Validate schema
      expect(transaction.channel).toBe('gumroad');
      expect(transaction.amount_usd).toBe(24.99);
      expect(transaction.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
      expect(transaction.source_id).toContain('gumroad_');
      expect(transaction.description).toContain('Gumroad sale');
      expect(transaction.content_id).toBe('prod_schema_test');
      expect(transaction.metadata.purchaser_email).toBe('schema@example.com');
      expect(transaction.metadata.product_name).toBe('Schema Test');
      expect(transaction.metadata.license_key).toBe('LICENSE_schema');
      expect(transaction.metadata.variant).toBe('PDF');
    });
  });

  describe('Edge Cases', () => {
    it('should handle variant title as product name fallback', async () => {
      const payload = {
        product_id: 'prod_variant_fallback',
        // No product_name
        product_name: undefined,
        variant_title: 'Premium Edition',
        price: '59.99',
        purchase_email: 'variant@example.com',
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.product_name).toBeDefined();
    });

    it('should handle legacy purchaser object format', async () => {
      const payload = {
        product_id: 'prod_legacy_format',
        product_name: 'Legacy Format Test',
        price: '19.99',
        purchaser: {
          email: 'legacy@example.com',
          name: 'Legacy User',
        },
        // No purchase_email at top level
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.purchaser_email).toBe('legacy@example.com');
    });

    it('should generate unique transaction IDs', async () => {
      const payload = {
        product_id: 'prod_unique_test',
        product_name: 'Unique Test',
        price: '9.99',
        purchase_email: 'unique@example.com',
      };

      // Send same payload twice
      const response1 = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data1 = await response1.json();

      // Wait a second to ensure different timestamp
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const response2 = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data2 = await response2.json();

      // Transaction IDs should be different even for same product
      expect(data1.transaction_id).not.toBe(data2.transaction_id);
    });
  });
});
