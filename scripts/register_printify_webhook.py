#!/usr/bin/env python3
"""
Register Printify API webhook for real-time POD order tracking.

Usage:
    python3 scripts/register_printify_webhook.py [--shop-id SHOP_ID] [--remove WEBHOOK_ID]

Environment variables required:
    PRINTIFY_API_TOKEN - Printify API access token
    PUBLIC_SITE_URL or DOMAIN - Base URL for webhook (default: https://profitengine.alreadyherellc.com)

Examples:
    # Register webhook for first shop
    python3 scripts/register_printify_webhook.py

    # Register webhook for specific shop
    python3 scripts/register_printify_webhook.py --shop-id 12345678

    # Remove webhook
    python3 scripts/register_printify_webhook.py --remove webhook_id_here
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'


def load_env():
    """Load environment variables from .env file if not already set."""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value


def get_api_token() -> str:
    """Get Printify API token from environment."""
    token = os.environ.get('PRINTIFY_API_TOKEN')
    if not token:
        print(f"{RED}❌ Error: PRINTIFY_API_TOKEN not found in environment{END}")
        print(f"{YELLOW}Set it in .env or export it: export PRINTIFY_API_TOKEN='your-token'{END}")
        sys.exit(1)
    return token


def get_domain() -> str:
    """Get domain from environment or use default."""
    domain = os.environ.get('PUBLIC_SITE_URL') or os.environ.get('DOMAIN')
    if not domain:
        domain = 'https://profitengine.alreadyherellc.com'
    return domain.rstrip('/')


def make_request(
    method: str,
    url: str,
    token: str,
    data: Optional[Dict] = None,
    timeout: int = 15
) -> Tuple[int, Dict]:
    """Make HTTP request to Printify API."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'ProfitEngine/5.0'
    }

    req_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            return response.status, response_data
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode('utf-8'))
        except:
            error_data = {'error': str(e)}
        return e.code, error_data
    except urllib.error.URLError as e:
        return 0, {'error': str(e)}


def get_shops(token: str) -> List[Dict]:
    """Get list of Printify shops."""
    status, response = make_request('GET', 'https://api.printify.com/v1/shops.json', token)

    if status != 200:
        print(f"{RED}❌ Failed to get shops: {response}{END}")
        sys.exit(1)

    return response if isinstance(response, list) else response.get('shops', [])


def select_shop(token: str, shop_id: Optional[str] = None) -> Dict:
    """Select a shop from available shops."""
    shops = get_shops(token)

    if not shops:
        print(f"{RED}❌ No shops found. Create one at https://printify.com{END}")
        sys.exit(1)

    if shop_id:
        shop = next((s for s in shops if str(s['id']) == str(shop_id)), None)
        if not shop:
            print(f"{RED}❌ Shop ID {shop_id} not found{END}")
            print(f"\n{YELLOW}Available shops:{END}")
            for s in shops:
                print(f"  - ID: {s['id']:15} Name: {s['title']}")
            sys.exit(1)
        return shop

    if len(shops) == 1:
        return shops[0]

    # Prompt user to select
    print(f"\n{BLUE}Available Printify shops:{END}")
    for i, s in enumerate(shops, 1):
        print(f"  {i}. {s['title']} (ID: {s['id']})")

    while True:
        try:
            choice = int(input(f"\n{BLUE}Select shop (1-{len(shops)}): {END}"))
            if 1 <= choice <= len(shops):
                return shops[choice - 1]
        except (ValueError, KeyboardInterrupt):
            pass
        print(f"{YELLOW}Invalid selection. Try again.{END}")


def get_existing_webhooks(token: str, shop_id: int) -> List[Dict]:
    """Get existing webhooks for a shop."""
    status, response = make_request(
        'GET',
        f'https://api.printify.com/v1/shops/{shop_id}/webhooks.json',
        token
    )

    if status != 200:
        return []

    return response if isinstance(response, list) else response.get('webhooks', [])


def register_webhook(token: str, shop_id: int, domain: str) -> Tuple[bool, Dict]:
    """Register order tracking webhook with Printify API."""
    webhook_url = f'{domain}/api/webhooks/printify'

    # Check existing webhooks
    existing = get_existing_webhooks(token, shop_id)
    for webhook in existing:
        if webhook.get('address') == webhook_url and webhook.get('topic') == 'order:created':
            print(f"{YELLOW}⚠️  Webhook already registered:{END}")
            print(f"   ID: {webhook['id']}")
            print(f"   URL: {webhook.get('address')}")
            return True, webhook

    # Register new webhook
    payload = {
        'topic': 'order:created',
        'address': webhook_url
    }

    status, response = make_request(
        'POST',
        f'https://api.printify.com/v1/shops/{shop_id}/webhooks.json',
        token,
        payload
    )

    if status == 201:
        print(f"{GREEN}✅ Webhook registered successfully!{END}")
        print(f"   ID: {response.get('id')}")
        print(f"   Topic: {response.get('topic')}")
        print(f"   URL: {response.get('address')}")
        print(f"   Status: {response.get('status')}")
        return True, response
    else:
        print(f"{RED}❌ Failed to register webhook: {response}{END}")
        return False, response


def remove_webhook(token: str, shop_id: int, webhook_id: str) -> bool:
    """Remove a webhook."""
    status, response = make_request(
        'DELETE',
        f'https://api.printify.com/v1/shops/{shop_id}/webhooks/{webhook_id}.json',
        token
    )

    if status == 204 or status == 200:
        print(f"{GREEN}✅ Webhook removed successfully!{END}")
        return True
    else:
        print(f"{RED}❌ Failed to remove webhook: {response}{END}")
        return False


def verify_webhook_endpoint(domain: str) -> bool:
    """Test that webhook endpoint is reachable."""
    test_payload = {
        'action': 'order.created',
        'data': {
            'id': '999999',
            'status': 'pending',
            'total_price': 99.99,
            'currency': 'USD',
            'line_items': [{'title': 'Test Product', 'quantity': 1}]
        }
    }

    url = f'{domain}/api/webhooks/printify'
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'ProfitEngine/5.0'
    }

    req_data = json.dumps(test_payload).encode('utf-8')
    req = urllib.request.Request(url, data=req_data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = response.status == 200
            status_msg = f"{GREEN}reachable{END}" if result else f"{YELLOW}partial{END}"
            print(f"   Webhook endpoint: {status_msg} (HTTP {response.status})")
            return True
    except urllib.error.HTTPError as e:
        # 400 is fine - endpoint exists and returns response
        if 400 <= e.code < 500:
            print(f"   Webhook endpoint: {GREEN}reachable{END} (HTTP {e.code})")
            return True
        print(f"   Webhook endpoint: {RED}unreachable{END} (HTTP {e.code})")
        return False
    except Exception as e:
        print(f"   Webhook endpoint: {RED}error{END} ({str(e)})")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Register Printify webhook for POD order tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--shop-id', help='Printify shop ID (optional, will prompt if not provided)')
    parser.add_argument('--remove', help='Remove webhook by ID instead of registering')
    parser.add_argument('--verify', action='store_true', help='Only verify webhook endpoint without registering')

    args = parser.parse_args()

    # Load environment
    load_env()

    # Get credentials
    token = get_api_token()
    domain = get_domain()

    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{BLUE}Printify Webhook Registration{END}")
    print(f"{BLUE}{'='*60}{END}\n")

    print(f"Domain: {domain}")
    print(f"Webhook URL: {domain}/api/webhooks/printify\n")

    # Verify endpoint if requested
    if args.verify:
        print(f"{BLUE}Verifying webhook endpoint...{END}")
        if verify_webhook_endpoint(domain):
            print(f"\n{GREEN}✅ Webhook endpoint is ready{END}")
        else:
            print(f"\n{RED}❌ Webhook endpoint verification failed{END}")
            print(f"{YELLOW}Ensure your backend/frontend is deployed to {domain}{END}")
        return

    # Remove webhook if requested
    if args.remove:
        shop = select_shop(token, args.shop_id)
        if remove_webhook(token, shop['id'], args.remove):
            print(f"\n{GREEN}✅ Cleanup complete{END}")
        sys.exit(0)

    # Register webhook
    print(f"{BLUE}Selecting shop...{END}")
    shop = select_shop(token, args.shop_id)
    print(f"{GREEN}✅ Selected: {shop['title']} (ID: {shop['id']}){END}\n")

    print(f"{BLUE}Registering webhook...{END}")
    success, webhook_data = register_webhook(token, shop['id'], domain)

    if success:
        print(f"\n{BLUE}Verifying webhook endpoint...{END}")
        verify_webhook_endpoint(domain)

        print(f"\n{GREEN}{'='*60}{END}")
        print(f"{GREEN}Webhook registration complete!{END}")
        print(f"{GREEN}{'='*60}{END}\n")

        print(f"{BLUE}Next steps:{END}")
        print(f"1. Printify will now send order events to your webhook")
        print(f"2. Orders will be logged to .runtime/revenue/transactions.jsonl")
        print(f"3. Monitor logs: tail -f .runtime/webhook.log")
        print()
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
