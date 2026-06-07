# Printify to Etsy Launch

Your Etsy shop can be connected while the API token still fails product publishing. A `403 Forbidden` from:

```text
POST /v1/uploads/images.json
```

means the Printify token does not have access to upload images. Printify documents 403 as protected-resource access without the needed API credentials. Image upload requires `uploads.write`; product creation requires `products.write`.

## Required Printify Token Scopes

Create or regenerate a Printify Personal Access Token with:

```text
shops.read
products.read
products.write
uploads.write
```

Recommended for this launch token:

```text
catalog.read
print_providers.read
uploads.read
uploads.write
products.read
products.write
shops.read
```

Then update GitHub Actions secret:

```text
PRINTIFY_API_TOKEN
```

Keep the existing:

```text
PRINTIFY_SHOP_ID=27823132
```

## Verify

Run:

```bash
python scripts/printify_shop_status.py
```

Then GitHub Actions:

```text
EAOS - POD Render & Printify Push
sku: leave blank
push_to_printify: true
```

Expected result:

```text
Done: 8/8 products pushed to Printify
```

If Etsy is connected in Printify, listings should sync from Printify to Etsy after publish.
