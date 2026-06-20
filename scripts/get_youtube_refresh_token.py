#!/usr/bin/env python3
"""Get YouTube Analytics API refresh token via OAuth 2.0 flow.

Interactive script to obtain a refresh token for offline YouTube Analytics access.

Usage:
    python scripts/get_youtube_refresh_token.py \
      --client-id YOUR_CLIENT_ID \
      --client-secret YOUR_CLIENT_SECRET
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from google.auth.oauthlib.flow import InstalledAppFlow
except ImportError:
    print("❌ google-auth-oauthlib not installed")
    print("   Install with: pip install google-auth-oauthlib")
    sys.exit(1)


def get_refresh_token(client_id: str, client_secret: str) -> str:
    """Get refresh token via OAuth 2.0 flow.

    Args:
        client_id: OAuth 2.0 Client ID
        client_secret: OAuth 2.0 Client Secret

    Returns:
        Refresh token string
    """
    # YouTube Analytics API scope
    SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]

    # Create credentials from client ID/secret
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": SCOPES,
        }
    }

    # Start OAuth flow
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("\n🔐 Opening browser for YouTube authorization...")

    creds = flow.run_local_server(port=0)

    if not creds.refresh_token:
        print("❌ Failed to obtain refresh token")
        return None

    print("\n✅ Authorization successful!")
    print(f"\n📋 Your refresh token:\n")
    print(f"   {creds.refresh_token}\n")

    return creds.refresh_token


def main():
    """Parse arguments and get refresh token."""
    parser = argparse.ArgumentParser(
        description="Get YouTube Analytics API refresh token"
    )

    parser.add_argument(
        "--client-id",
        required=True,
        help="OAuth 2.0 Client ID"
    )
    parser.add_argument(
        "--client-secret",
        required=True,
        help="OAuth 2.0 Client Secret"
    )

    args = parser.parse_args()

    try:
        token = get_refresh_token(args.client_id, args.client_secret)
        return 0 if token else 1
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
