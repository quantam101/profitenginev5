#!/usr/bin/env python3
"""
Test script to verify YouTube OAuth 2.0 credentials.

Validates that YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN
are correctly configured and can authenticate with YouTube API.

Usage:
    python test_youtube_credentials.py

Output:
    ✅ All credentials valid
    ❌ Missing or invalid credentials (with detailed error)
"""

import os
import sys
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: Google libraries not installed")
    print("Install with: pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)


def test_youtube_credentials() -> bool:
    """
    Test YouTube OAuth 2.0 credentials.

    Returns:
        True if credentials valid, False otherwise
    """
    print("\n" + "=" * 70)
    print("YouTube OAuth 2.0 Credential Validation")
    print("=" * 70 + "\n")

    # Step 1: Check environment variables
    print("[1/3] Checking environment variables...")

    client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

    if not client_id:
        print("  ❌ YOUTUBE_CLIENT_ID not set")
        return False
    print(f"  ✅ YOUTUBE_CLIENT_ID: {client_id[:20]}...")

    if not client_secret:
        print("  ❌ YOUTUBE_CLIENT_SECRET not set")
        return False
    print(f"  ✅ YOUTUBE_CLIENT_SECRET: {client_secret[:20]}...")

    if not refresh_token:
        print("  ❌ YOUTUBE_REFRESH_TOKEN not set")
        return False
    print(f"  ✅ YOUTUBE_REFRESH_TOKEN: {refresh_token[:20]}...")

    # Step 2: Test OAuth token refresh
    print("\n[2/3] Testing OAuth token refresh...")

    try:
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )

        request = Request()
        credentials.refresh(request)

        if not credentials.token:
            print("  ❌ Token refresh returned no access token")
            return False

        print(f"  ✅ Access token obtained (expires in {credentials.expiry})")

    except Exception as e:
        print(f"  ❌ Token refresh failed: {e}")
        print("\n     Possible causes:")
        print("       - YOUTUBE_REFRESH_TOKEN revoked or expired")
        print("       - YOUTUBE_CLIENT_ID/CLIENT_SECRET incorrect")
        print("       - Network error")
        print("\n     Solutions:")
        print("       1. Generate new refresh token: python get_youtube_refresh_token.py")
        print("       2. Check credentials: https://console.cloud.google.com/apis/credentials")
        return False

    # Step 3: Test YouTube API access
    print("\n[3/3] Testing YouTube API access...")

    try:
        youtube = build(
            "youtube",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

        # Try to get authenticated user's channel
        request = youtube.channels().list(
            part="snippet",
            mine=True,
            maxResults=1,
        )
        response = request.execute()

        if response.get("items"):
            channel = response["items"][0]
            channel_title = channel.get("snippet", {}).get("title", "Unknown")
            print(f"  ✅ YouTube API access granted")
            print(f"  ✅ Channel: {channel_title}")
        else:
            print("  ⚠️  YouTube API access granted but no channel found")
            print("     Make sure your YouTube account has a channel")
            return False

    except HttpError as e:
        error_msg = str(e)
        status_code = e.resp.status if hasattr(e, "resp") else "unknown"

        print(f"  ❌ YouTube API error ({status_code}): {error_msg[:200]}")

        if status_code == 403 or "forbidden" in error_msg.lower():
            print("\n     Access forbidden. Check:")
            print("       - YouTube account is in good standing")
            print("       - Channel exists and is accessible")
            print("       - OAuth consent screen configured for youtube.upload scope")
        elif status_code == 401 or "unauthorized" in error_msg.lower():
            print("\n     Unauthorized. Check:")
            print("       - Refresh token not revoked")
            print("       - Client ID/Secret correct")
        elif status_code == 404 or "not found" in error_msg.lower():
            print("\n     YouTube Data API v3 not found. Enable it:")
            print("       https://console.cloud.google.com/apis/library/youtube.googleapis.com")

        return False

    except Exception as e:
        print(f"  ❌ YouTube API test failed: {e}")
        return False

    return True


def main() -> None:
    """CLI entry point."""
    print("Testing YouTube OAuth 2.0 credentials...\n")

    success = test_youtube_credentials()

    print("\n" + "=" * 70)
    if success:
        print("✅ All tests passed! Ready to upload videos to YouTube.")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Test upload: python scripts/test_youtube_upload.py")
        print("  2. Or use: python scripts/social_media_publishers.py")
        sys.exit(0)
    else:
        print("❌ Credential validation failed. See errors above.")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("  1. Get new refresh token:")
        print("     python get_youtube_refresh_token.py")
        print("\n  2. Check Google Cloud Console:")
        print("     https://console.cloud.google.com/apis/credentials")
        print("\n  3. Enable YouTube Data API v3:")
        print("     https://console.cloud.google.com/apis/library/youtube.googleapis.com")
        print("\n  4. Set environment variables:")
        print("     export YOUTUBE_CLIENT_ID=...")
        print("     export YOUTUBE_CLIENT_SECRET=...")
        print("     export YOUTUBE_REFRESH_TOKEN=...")
        sys.exit(1)


if __name__ == "__main__":
    main()
