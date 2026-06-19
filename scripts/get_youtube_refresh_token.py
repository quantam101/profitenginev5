#!/usr/bin/env python3
"""
Helper script to obtain YouTube OAuth 2.0 refresh token.

This script runs the OAuth 2.0 flow to get a refresh token that can be used
for automated video uploads without user interaction.

The refresh token is long-lived and never expires unless explicitly revoked.

Usage:
    python get_youtube_refresh_token.py --credentials credentials.json

Or with default location:
    python get_youtube_refresh_token.py

This will:
1. Open your browser for Google sign-in
2. Ask for permission to upload videos
3. Print your YOUTUBE_REFRESH_TOKEN
4. Optionally save to .env file
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: google-auth-oauthlib not installed")
    print("Install with: pip install google-auth-oauthlib>=1.2.0")
    sys.exit(1)


def get_refresh_token(credentials_file: str = "credentials.json") -> str | None:
    """
    Run OAuth 2.0 flow to get refresh token.

    Args:
        credentials_file: Path to credentials.json from Google Cloud Console

    Returns:
        Refresh token string or None if failed
    """
    credentials_path = Path(credentials_file)

    if not credentials_path.exists():
        print(f"ERROR: Credentials file not found: {credentials_path}")
        print("\nTo get credentials.json:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop application)")
        print("3. Click the credential to open it")
        print("4. Click 'Download JSON'")
        print("5. Save as credentials.json")
        return None

    try:
        print(f"[INFO] Loading credentials from: {credentials_path}")

        # YouTube API scope for uploading videos
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]

        # Run OAuth flow (opens browser for user to sign in)
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            scopes=scopes,
        )

        print("\n[INFO] Opening browser for Google sign-in...")
        print("[INFO] You will be asked to:")
        print("  1. Sign in with your Google account")
        print("  2. Grant permission to upload videos to YouTube")
        print("  3. Authorize the app")
        print("\nWaiting for authorization...")

        creds = flow.run_local_server(port=0)

        if not creds.refresh_token:
            print("\nERROR: No refresh token in credentials")
            print("This can happen if:")
            print("  - You selected a pre-existing client ID instead of new")
            print("  - OAuth consent screen not configured for YouTube scope")
            print("\nTry:")
            print("  1. Delete the old credential")
            print("  2. Create a NEW OAuth 2.0 Client ID (Desktop application)")
            print("  3. Download the new credentials.json")
            print("  4. Run this script again")
            return None

        print("\n" + "=" * 70)
        print("SUCCESS! Your YouTube refresh token:")
        print("=" * 70)
        print(f"\nYOUTUBE_REFRESH_TOKEN={creds.refresh_token}\n")
        print("=" * 70)
        print("\nStore this token in:")
        print("  1. GitHub Secrets (for CI/CD)")
        print("  2. OCI server .env file (for runtime)")
        print("  3. Vercel environment variables (if using frontend)")
        print("\nThe refresh token:")
        print("  - Never expires (unless you revoke it)")
        print("  - Should be kept secure")
        print("  - Can be used to upload videos without user interaction")
        print("  - Should be rotated quarterly for security")

        return creds.refresh_token

    except Exception as e:
        print(f"\nERROR: OAuth flow failed: {e}")
        print("\nTroubleshooting:")
        print("  - Make sure credentials.json is valid (from Google Cloud Console)")
        print("  - Check that YouTube Data API v3 is enabled")
        print("  - Try deleting credentials.json and getting a new one")
        return None


def get_client_credentials(credentials_file: str = "credentials.json") -> tuple[str, str] | tuple[None, None]:
    """
    Extract CLIENT_ID and CLIENT_SECRET from credentials.json.

    Args:
        credentials_file: Path to credentials.json

    Returns:
        Tuple of (CLIENT_ID, CLIENT_SECRET) or (None, None) if failed
    """
    credentials_path = Path(credentials_file)

    if not credentials_path.exists():
        return None, None

    try:
        data = json.loads(credentials_path.read_text())
        client_id = data.get("installed", {}).get("client_id")
        client_secret = data.get("installed", {}).get("client_secret")
        return client_id, client_secret
    except Exception:
        return None, None


def save_to_env(refresh_token: str, client_id: str, client_secret: str, env_file: str = ".env") -> None:
    """
    Append credentials to .env file.

    Args:
        refresh_token: YouTube refresh token
        client_id: OAuth 2.0 Client ID
        client_secret: OAuth 2.0 Client Secret
        env_file: Path to .env file
    """
    env_path = Path(env_file)

    content = f"""# YouTube OAuth 2.0 Credentials
YOUTUBE_CLIENT_ID={client_id}
YOUTUBE_CLIENT_SECRET={client_secret}
YOUTUBE_REFRESH_TOKEN={refresh_token}
"""

    if env_path.exists():
        existing = env_path.read_text()
        if "YOUTUBE_" in existing:
            print(f"\n[WARNING] .env already contains YouTube credentials")
            print("Update them manually or remove old values first")
            return

        env_path.write_text(existing.rstrip() + "\n\n" + content)
        print(f"\n[OK] Appended to {env_file}")
    else:
        env_path.write_text(content)
        print(f"\n[OK] Created {env_file}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Get YouTube OAuth 2.0 refresh token",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python get_youtube_refresh_token.py
  python get_youtube_refresh_token.py --credentials credentials.json
  python get_youtube_refresh_token.py --save-env
  python get_youtube_refresh_token.py --credentials creds.json --save-env
        """,
    )

    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Path to credentials.json (default: credentials.json)",
    )

    parser.add_argument(
        "--save-env",
        action="store_true",
        help="Append credentials to .env file",
    )

    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("YouTube OAuth 2.0 Refresh Token Generator")
    print("=" * 70 + "\n")

    # Get refresh token
    refresh_token = get_refresh_token(args.credentials)
    if not refresh_token:
        sys.exit(1)

    # Optionally extract and save client credentials
    if args.save_env:
        client_id, client_secret = get_client_credentials(args.credentials)
        if client_id and client_secret:
            save_to_env(refresh_token, client_id, client_secret, args.env_file)
        else:
            print(f"\n[WARNING] Could not extract CLIENT_ID/CLIENT_SECRET from {args.credentials}")
            print("Add them manually to .env:")
            print(f"  YOUTUBE_CLIENT_ID=...")
            print(f"  YOUTUBE_CLIENT_SECRET=...")
            print(f"  YOUTUBE_REFRESH_TOKEN={refresh_token}")

    print("\n[INFO] Next steps:")
    print("  1. Copy YOUTUBE_REFRESH_TOKEN above")
    print("  2. Add to GitHub Secrets")
    print("  3. Add to OCI server .env")
    print("  4. Redeploy")
    print("  5. Test with: python scripts/test_youtube_credentials.py")


if __name__ == "__main__":
    main()
