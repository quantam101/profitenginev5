"""
Gumroad API service for syncing ebook sales and product inventory.

Handles:
- Real-time webhook processing for product sales
- Product inventory sync from Gumroad
- Revenue tracking and reporting
- License key management for digital products
"""
import os
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

GUMROAD_API_BASE = "https://api.gumroad.com/v2"


class GumroadSale(BaseModel):
    """Gumroad product sale record."""
    product_id: str
    product_name: str
    amount_usd: float
    purchaser_email: str
    license_key: Optional[str] = None
    variant_title: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_transaction(self) -> Dict[str, Any]:
        """Convert to transaction log format."""
        return {
            "channel": "gumroad",
            "amount_usd": self.amount_usd,
            "timestamp": self.timestamp,
            "source_id": self.source_id or f"gumroad_{self.product_id}_{int(datetime.fromisoformat(self.timestamp).timestamp())}",
            "description": f"Gumroad sale: {self.product_name}",
            "content_id": self.product_id,
            "metadata": {
                "purchaser_email": self.purchaser_email,
                "product_name": self.product_name,
                "license_key": self.license_key,
                "variant": self.variant_title,
                **self.metadata,
            },
        }


class GumroadProduct(BaseModel):
    """Gumroad product from inventory."""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "usd"
    file_key: Optional[str] = None
    published_at: Optional[str] = None
    url_slug: Optional[str] = None
    license_expiration_interval: Optional[int] = None
    license_expiration_interval_unit: Optional[str] = None


class GumroadService:
    """Service for managing Gumroad integration."""

    def __init__(self):
        self.access_token = os.environ.get("GUMROAD_ACCESS_TOKEN")
        self.seller_id = os.environ.get("GUMROAD_SELLER_ID")

        if not self.access_token:
            raise ValueError("GUMROAD_ACCESS_TOKEN not configured in .env")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def fetch_products(self) -> List[GumroadProduct]:
        """Fetch all products from Gumroad account."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GUMROAD_API_BASE}/products",
                    headers=self.headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                products = []
                for product_data in data.get("products", []):
                    products.append(GumroadProduct(**product_data))

                return products
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to fetch Gumroad products: {e}")

    async def fetch_sales(self, product_id: Optional[str] = None) -> List[GumroadSale]:
        """
        Fetch sales for a specific product or all products.

        Args:
            product_id: Optional product ID to filter sales

        Returns:
            List of GumroadSale objects
        """
        try:
            async with httpx.AsyncClient() as client:
                endpoint = f"{GUMROAD_API_BASE}/sales"
                params = {}
                if product_id:
                    params["product_id"] = product_id

                response = await client.get(
                    endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                sales = []
                for sale_data in data.get("sales", []):
                    sale = GumroadSale(
                        product_id=sale_data.get("product_id", ""),
                        product_name=sale_data.get("product_name", ""),
                        amount_usd=float(sale_data.get("price", 0)),
                        purchaser_email=sale_data.get("purchase_email", ""),
                        license_key=sale_data.get("license_key"),
                        variant_title=sale_data.get("variant_title"),
                        timestamp=sale_data.get("created_at", datetime.utcnow().isoformat()),
                    )
                    sales.append(sale)

                return sales
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to fetch Gumroad sales: {e}")

    async def verify_license(self, product_id: str, license_key: str) -> bool:
        """
        Verify a license key for a product.

        Args:
            product_id: Gumroad product ID
            license_key: License key to verify

        Returns:
            True if license is valid, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{GUMROAD_API_BASE}/licenses/verify",
                    headers=self.headers,
                    json={
                        "product_id": product_id,
                        "license_key": license_key,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("success", False)
        except httpx.RequestError as e:
            print(f"Failed to verify license: {e}")
            return False

    def parse_webhook_payload(self, payload: Dict[str, Any]) -> GumroadSale:
        """
        Parse webhook payload from Gumroad.

        Gumroad sends the following in the webhook:
        - product_id
        - product_name
        - price (in cents, so divide by 100)
        - purchase_email
        - license_key (if product has licenses)
        - variant_title (if product has variants)
        - timestamp (ISO format)

        Args:
            payload: Raw webhook payload from Gumroad

        Returns:
            Parsed GumroadSale object
        """
        # Gumroad price is in cents for most currencies, but USD prices are in dollars
        amount = payload.get("price", 0)
        if isinstance(amount, str):
            amount = float(amount)

        # Handle both cent and dollar amounts
        if amount > 10000:  # Likely in cents
            amount = amount / 100

        return GumroadSale(
            product_id=payload.get("product_id", ""),
            product_name=payload.get("product_name", payload.get("variant_title", "Unknown")),
            amount_usd=amount,
            purchaser_email=payload.get("purchase_email", payload.get("purchaser", {}).get("email", "unknown")),
            license_key=payload.get("license_key"),
            variant_title=payload.get("variant_title"),
            timestamp=payload.get("timestamp", datetime.utcnow().isoformat()),
        )

    async def get_product_info(self, product_id: str) -> Optional[GumroadProduct]:
        """
        Get detailed info for a specific product.

        Args:
            product_id: Gumroad product ID

        Returns:
            GumroadProduct object or None if not found
        """
        try:
            products = await self.fetch_products()
            for product in products:
                if product.id == product_id:
                    return product
            return None
        except Exception as e:
            print(f"Failed to get product info: {e}")
            return None


# Singleton instance
_gumroad_service: Optional[GumroadService] = None


def get_gumroad_service() -> GumroadService:
    """Get or create the Gumroad service singleton."""
    global _gumroad_service
    if _gumroad_service is None:
        _gumroad_service = GumroadService()
    return _gumroad_service
