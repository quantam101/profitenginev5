#!/usr/bin/env python3
"""
Social Media Publishers for ProfitEngine Content Distribution

Production-ready OAuth 2.0 integrations for:
- Twitter/X (OAuth 2.0 with tweepy)
- Reddit (OAuth 2.0 with PRAW)
- LinkedIn (OAuth 2.0 REST API)
- Facebook (Graph API with page access token)
- Instagram (Graph API with business account)
- TikTok (OAuth 2.0 with business account)

All functions follow the same pattern:
  def publish_PLATFORM(article: Dict, canonical_url: str) -> Optional[str]
  Returns: URL of published post, or None if skipped/failed

Credentials are read from environment variables and must be rotated regularly.
See: SECURITY_ROTATION_REQUIRED.md for credential rotation procedures.
"""
from __future__ import annotations

import os
import json
import logging
import re
import base64
from typing import Any, Dict, Optional, List
import httpx

logger = logging.getLogger(__name__)

# ── Environment Variables (OAuth 2.0 + API Keys) ──────────────────────────────
# Read at function call time, not import time, to allow test fixtures to set env vars

def _get_env(key: str, default: str = "") -> str:
  return os.getenv(key, default).strip()

# Global HTTP client with reasonable timeouts
http_client = httpx.AsyncClient(timeout=30.0)

# ── Twitter/X Publishing (OAuth 2.0) ───────────────────────────────────────

def publish_twitter(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    """
    Publish article summary to Twitter/X using OAuth 2.0.

    Requires: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN,
              TWITTER_ACCESS_SECRET, or TWITTER_BEARER_TOKEN

    Uses tweepy v4.14+ for OAuth 2.0 support.
    """
    api_key = _get_env("TWITTER_API_KEY")
    api_secret = _get_env("TWITTER_API_SECRET")
    bearer_token = _get_env("TWITTER_BEARER_TOKEN")
    access_token = _get_env("TWITTER_ACCESS_TOKEN")
    access_secret = _get_env("TWITTER_ACCESS_SECRET")

    if not api_key or not api_secret:
        logger.info("[SKIP] Twitter: API credentials not configured")
        return None

    try:
        import tweepy
    except ImportError:
        logger.warning("[SKIP] Twitter: tweepy not installed (pip install tweepy>=4.14.0)")
        return None

    try:
        title = article.get("title", "")
        meta = article.get("meta_description", "")

        # Build tweet: title (truncated) + meta snippet + URL
        # Twitter v2 allows 280 characters per tweet
        tweet_text = f"{title}\n\n{meta}"[:240] + f"\n\n{canonical_url}"

        # Use OAuth 2.0 v2 Client if bearer token available (preferred)
        if bearer_token:
            client = tweepy.Client(bearer_token=bearer_token)
        else:
            # Fall back to OAuth 1.0a user context (API key + secret + tokens)
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )

        # Post the tweet
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data.get("id") if response.data else None

        if tweet_id:
            # Twitter username lookup required for full URL; use ID-based format
            url = f"https://twitter.com/i/web/status/{tweet_id}"
            logger.info(f"[OK] Published to Twitter: {url}")
            return url
        else:
            logger.error("[FAIL] Twitter: No tweet ID in response")
            return None

    except tweepy.TweepyException as e:
        logger.error(f"[FAIL] Twitter: {e.response.text if hasattr(e, 'response') else str(e)}")
        return None
    except Exception as e:
        logger.error(f"[FAIL] Twitter: {type(e).__name__}: {str(e)}")
        return None


# ── Reddit Publishing (OAuth 2.0 via PRAW) ─────────────────────────────────

def publish_reddit(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    """
    Post article to Reddit subreddit using OAuth 2.0.

    Requires: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME,
              REDDIT_PASSWORD, REDDIT_SUBREDDIT

    Uses PRAW v7.7+ for OAuth 2.0 support.
    See: https://praw.readthedocs.io/en/latest/
    """
    client_id = _get_env("REDDIT_CLIENT_ID")
    client_secret = _get_env("REDDIT_CLIENT_SECRET")
    username = _get_env("REDDIT_USERNAME")
    password = _get_env("REDDIT_PASSWORD")
    subreddit = _get_env("REDDIT_SUBREDDIT")

    if not all([client_id, client_secret, username, password, subreddit]):
        logger.info(f"[SKIP] Reddit: Missing credentials (ID={bool(client_id)}, secret={bool(client_secret)}, user={bool(username)}, pass={bool(password)}, sub={bool(subreddit)})")
        return None

    try:
        import praw
    except ImportError:
        logger.warning("[SKIP] Reddit: praw not installed (pip install praw>=7.7.0)")
        return None

    try:
        title = article.get("title", "")
        meta = article.get("meta_description", "")

        # Reddit title limit: 300 characters
        if len(title) > 300:
            title = title[:297] + "..."

        # Initialize Reddit OAuth 2.0 client
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=f"ProfitEngine/1.0 (posting by {username})",
            username=username,
            password=password,
            # OAuth 2.0 flow is automatic with username/password
        )

        # Verify authentication
        try:
            _ = reddit.user.me()
        except praw.exceptions.InvalidToken:
            logger.error("[FAIL] Reddit: Invalid OAuth 2.0 credentials")
            return None

        # Submit as link post
        subreddit_obj = reddit.subreddit(subreddit)
        submission = subreddit_obj.submit(
            title=title,
            url=canonical_url,
        )

        url = f"https://reddit.com{submission.permalink}"
        logger.info(f"[OK] Published to Reddit: {url}")
        return url

    except praw.exceptions.PRAWException as e:
        logger.error(f"[FAIL] Reddit PRAW: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[FAIL] Reddit: {type(e).__name__}: {str(e)}")
        return None


# ── LinkedIn Publishing (OAuth 2.0 REST API) ────────────────────────────────

def publish_linkedin(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    """
    Share article on LinkedIn using OAuth 2.0 REST API.

    Requires: LINKEDIN_ACCESS_TOKEN and either LINKEDIN_PERSON_URN
              (for personal profile) or LINKEDIN_ORGANIZATION_URN (for company page)

    LinkedIn API v2 (UGC Posts): https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management
    """
    access_token = _get_env("LINKEDIN_ACCESS_TOKEN")
    person_urn = _get_env("LINKEDIN_PERSON_URN")
    org_urn = _get_env("LINKEDIN_ORGANIZATION_URN")

    if not access_token:
        logger.info("[SKIP] LinkedIn: Access token not configured")
        return None

    if not person_urn and not org_urn:
        logger.info("[SKIP] LinkedIn: Neither LINKEDIN_PERSON_URN nor LINKEDIN_ORGANIZATION_URN configured")
        return None

    try:
        title = article.get("title", "")
        meta = article.get("meta_description", "")

        # Build share content: title + description + link
        share_text = f"{title}\n\n{meta}\n\nRead more: {canonical_url}"

        # Extract ID from URN format (urn:li:person:12345 -> 12345)
        author_urn = None
        if person_urn:
            person_id = person_urn.split(":")[-1] if ":" in person_urn else person_urn
            author_urn = f"urn:li:person:{person_id}"
        elif org_urn:
            org_id = org_urn.split(":")[-1] if ":" in org_urn else org_urn
            author_urn = f"urn:li:organization:{org_id}"

        # LinkedIn UGC Share endpoint payload
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.Share": {
                    "media": [
                        {
                            "status": "READY",
                            "media": canonical_url,
                            "type": "ARTICLE",
                        }
                    ],
                    "shareCommentary": {
                        "text": share_text,
                    },
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
            },
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202401",
            "User-Agent": "ProfitEngine/1.0",
        }

        r = httpx.post(
            "https://api.linkedin.com/rest/posts",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if r.status_code == 201:
            post_data = r.json()
            post_id = post_data.get("id", "")
            if post_id:
                url = f"https://www.linkedin.com/feed/update/{post_id}"
                logger.info(f"[OK] Published to LinkedIn: {url}")
                return url

        logger.error(f"[FAIL] LinkedIn {r.status_code}: {r.text[:300]}")
        return None

    except Exception as e:
        logger.error(f"[FAIL] LinkedIn: {type(e).__name__}: {str(e)}")
        return None


# ── Facebook Publishing (Graph API v18.0) ──────────────────────────────────

def publish_facebook(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    """
    Post article to Facebook page using Graph API.

    Requires: FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN

    The page access token must have pages_manage_posts permission.
    See: https://developers.facebook.com/docs/graph-api/reference/page/feed/
    """
    page_id = _get_env("FB_PAGE_ID")
    page_token = _get_env("FB_PAGE_ACCESS_TOKEN")

    if not page_id or not page_token:
        logger.info(f"[SKIP] Facebook: Missing credentials (ID={bool(page_id)}, token={bool(page_token)})")
        return None

    try:
        title = article.get("title", "")
        meta = article.get("meta_description", "")

        # Facebook Feed Post payload (message + link with auto-generated preview)
        payload = {
            "message": f"{title}\n\n{meta}",
            "link": canonical_url,
            "access_token": page_token,
        }

        # Graph API v18.0 (latest stable)
        r = httpx.post(
            f"https://graph.facebook.com/v18.0/{page_id}/feed",
            data=payload,
            timeout=30,
        )

        if r.status_code == 200:
            response = r.json()
            post_id = response.get("id", "")
            if post_id:
                # Format: page_id_post_id
                url = f"https://facebook.com/{post_id}"
                logger.info(f"[OK] Published to Facebook: {url}")
                return url

        error_msg = r.json().get("error", {}).get("message", r.text[:300]) if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]
        logger.error(f"[FAIL] Facebook {r.status_code}: {error_msg}")
        return None

    except Exception as e:
        logger.error(f"[FAIL] Facebook: {type(e).__name__}: {str(e)}")
        return None


# ── Instagram Publishing (Graph API v18.0, Business Account) ─────────────────

def publish_instagram(article: Dict[str, Any], image_url: str = "") -> Optional[str]:
    """
    Post article to Instagram using Graph API (requires business account).

    Requires: ig_user_id (Instagram Business Account ID) and FB_PAGE_ACCESS_TOKEN
              with instagram_content_publish permission

    Two-step process:
    1. Create media container with image_url and caption
    2. Publish the media container

    See: https://developers.facebook.com/docs/instagram-api/guides/content-publishing
    """
    ig_user_id = _get_env("ig_user_id")
    page_token = _get_env("FB_PAGE_ACCESS_TOKEN")

    if not ig_user_id or not page_token:
        logger.info(f"[SKIP] Instagram: Missing credentials (user_id={bool(ig_user_id)}, token={bool(page_token)})")
        return None

    if not image_url:
        logger.info("[SKIP] Instagram: Requires image_url (direct upload or public URL)")
        return None

    try:
        title = article.get("title", "")

        # Caption with hashtags and link bio CTA
        caption = f"{title}\n\nRead more in link bio 🔗"

        # Step 1: Create media container
        create_payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": page_token,
        }

        r = httpx.post(
            f"https://graph.instagram.com/v18.0/{ig_user_id}/media",
            data=create_payload,
            timeout=30,
        )

        if r.status_code != 200:
            error_msg = r.json().get("error", {}).get("message", r.text[:300]) if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]
            logger.error(f"[FAIL] Instagram create media {r.status_code}: {error_msg}")
            return None

        media_id = r.json().get("id", "")
        if not media_id:
            logger.error("[FAIL] Instagram: No media_id in create response")
            return None

        # Step 2: Publish the media container
        publish_payload = {
            "creation_id": media_id,
            "access_token": page_token,
        }

        publish_r = httpx.post(
            f"https://graph.instagram.com/v18.0/{ig_user_id}/media_publish",
            data=publish_payload,
            timeout=30,
        )

        if publish_r.status_code == 200:
            published_id = publish_r.json().get("id", media_id)
            # Note: Instagram doesn't provide direct URLs via API; use account handle
            url = f"https://instagram.com/p/{published_id}"
            logger.info(f"[OK] Published to Instagram: {published_id}")
            return url

        error_msg = publish_r.json().get("error", {}).get("message", publish_r.text[:300]) if publish_r.headers.get("content-type", "").startswith("application/json") else publish_r.text[:300]
        logger.error(f"[FAIL] Instagram publish media {publish_r.status_code}: {error_msg}")
        return None

    except Exception as e:
        logger.error(f"[FAIL] Instagram: {type(e).__name__}: {str(e)}")
        return None


# ── TikTok Publishing (OAuth 2.0, Business Account) ──────────────────────────

def publish_tiktok(article: Dict[str, Any], video_url: str = "") -> Optional[str]:
    """
    Post video to TikTok using OAuth 2.0 Open API.

    Requires: TIKTOK_ACCESS_TOKEN and TIKTOK_OPEN_ID (TikTok Business Account)

    TikTok Business Account can publish videos via:
    1. Direct upload endpoint (video_upload endpoint)
    2. Video URL publishing (requires video hosting)

    Note: TikTok's API is rate-limited; check current tier:
    https://developers.tiktok.com/doc/embed-videos
    """
    access_token = _get_env("TIKTOK_ACCESS_TOKEN")
    open_id = _get_env("TIKTOK_OPEN_ID")

    if not access_token:
        logger.info("[SKIP] TikTok: Access token not configured")
        return None

    if not open_id:
        logger.warning("[SKIP] TikTok: TIKTOK_OPEN_ID not configured (required for publishing)")
        return None

    if not video_url:
        logger.info("[SKIP] TikTok: Requires video_url (HTTPS, .mp4 or .mov, max 287MB)")
        return None

    try:
        title = article.get("title", "")

        # TikTok caption with hashtags (max 2200 chars)
        caption = f"{title}\n\n#profitengine #finance #investing"[:2200]

        # TikTok Open API v1 video upload endpoint
        # This initiates a video upload request (returns upload URL for file upload)
        payload = {
            "video_url": video_url,
            "caption": caption,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "ProfitEngine/1.0",
        }

        # Step 1: Request video upload
        r = httpx.post(
            f"https://open-api.tiktok.com/v1/video/upload/",
            json=payload,
            headers=headers,
            timeout=60,
        )

        if r.status_code == 200:
            response = r.json()
            # Check for TikTok API error codes
            if response.get("code") != 0:
                error_desc = response.get("message", "Unknown error")
                logger.error(f"[FAIL] TikTok API error: {error_desc}")
                return None

            data = response.get("data", {})
            video_id = data.get("video_id", "") or data.get("publish_id", "")

            if video_id:
                # TikTok video URL format (requires username)
                url = f"https://www.tiktok.com/@profitengine/video/{video_id}" if "@" in data.get("video_url", "") else f"https://tiktok.com/v/{video_id}"
                logger.info(f"[OK] Published to TikTok: {video_id}")
                return url

            logger.error("[FAIL] TikTok: No video_id in response")
            return None

        error_msg = r.json().get("message", r.text[:300]) if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]
        logger.error(f"[FAIL] TikTok {r.status_code}: {error_msg}")
        return None

    except Exception as e:
        logger.error(f"[FAIL] TikTok: {type(e).__name__}: {str(e)}")
        return None


# ── YouTube Publishing (OAuth 2.0 with Refresh Token) ─────────────────────────

def publish_youtube(article: Dict[str, Any], video_path: str = "") -> Optional[str]:
    """
    Upload video to YouTube using OAuth 2.0 with refresh token.

    Full implementation with:
    - OAuth 2.0 token refresh
    - Resumable video upload (chunked, resumable on network error)
    - Metadata: title, description, tags, category
    - Privacy: unlisted by default (change in code for public)
    - Progress logging during upload
    - Automatic retry on transient errors

    Requires: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN

    Initial OAuth 2.0 setup:
    1. Go to https://console.cloud.google.com/apis/credentials
    2. Create OAuth 2.0 Client ID (Desktop/Web app)
    3. Download credentials JSON
    4. Run OAuth flow to get refresh token:
       python -c "from google_auth_oauthlib.flow import InstalledAppFlow; flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes=['https://www.googleapis.com/auth/youtube.upload']); creds = flow.run_local_server(); print('Refresh token:', creds.refresh_token)"
    5. Store YOUTUBE_REFRESH_TOKEN in GitHub Secrets and OCI .env
    """
    client_id = _get_env("YOUTUBE_CLIENT_ID")
    client_secret = _get_env("YOUTUBE_CLIENT_SECRET")
    refresh_token = _get_env("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        logger.info(f"[SKIP] YouTube: Missing OAuth 2.0 credentials (ID={bool(client_id)}, secret={bool(client_secret)}, refresh={bool(refresh_token)})")
        return None

    if not video_path or not os.path.exists(video_path):
        logger.info(f"[SKIP] YouTube: Requires valid video_path (not found: {video_path})")
        return None

    # Verify video file is readable and has size
    try:
        video_size = os.path.getsize(video_path)
        if video_size < 1024:  # At least 1KB
            logger.error(f"[FAIL] YouTube: Video file too small ({video_size} bytes)")
            return None
    except OSError as e:
        logger.error(f"[FAIL] YouTube: Cannot read video file: {e}")
        return None

    try:
        # Import Google API client libraries
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
        from googleapiclient.errors import HttpError
        import io
    except ImportError:
        logger.warning("[SKIP] YouTube: google-auth-oauthlib or google-api-python-client not installed")
        logger.warning("Install with: pip install google-auth-oauthlib>=1.2.0 google-api-python-client>=2.108.0")
        return None

    try:
        title = article.get("title", "")
        meta = article.get("meta_description", "")
        body = article.get("body", "")[:5000]

        if not title:
            title = "ProfitEngine Article Video"

        # Ensure we have a title and description
        if not meta:
            meta = "Watch the full article on ProfitEngine"

        # Step 1: Refresh OAuth 2.0 credentials
        logger.debug("[YouTube] Refreshing OAuth 2.0 credentials...")
        credentials = Credentials(
            token=None,  # Will be refreshed from refresh_token
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )

        # Refresh the access token if expired (or always refresh to be safe)
        request = Request()
        try:
            credentials.refresh(request)
        except Exception as e:
            logger.error(f"[FAIL] YouTube: OAuth token refresh failed: {e}")
            return None

        # Step 2: Initialize YouTube API client with credentials
        logger.debug("[YouTube] Initializing YouTube API client...")
        youtube = build(
            "youtube",
            "v3",
            credentials=credentials,
            cache_discovery=False,  # Skip discovery cache to avoid permission issues
        )

        # Step 3: Prepare video metadata
        video_description = f"{meta}\n\n"
        if body:
            video_description += f"{body}\n\n"
        video_description += "\nFull article: https://profitengine.alreadyherellc.com"

        # Limit description to 5000 characters (YouTube limit)
        video_description = video_description[:5000]

        metadata = {
            "snippet": {
                "title": title[:100],  # YouTube title limit: 100 chars
                "description": video_description,
                "tags": ["finance", "investing", "profitengine", "markets", "trading"],
                "categoryId": "22",  # 22 = People & Blogs (appropriate for finance content)
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "unlisted",  # unlisted = not searchable but accessible via link
                "selfDeclaredMadeForKids": False,
                "madeForKids": False,
            },
        }

        # Step 4: Prepare resumable media upload
        logger.debug(f"[YouTube] Preparing media upload ({video_size} bytes)...")
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,  # 10MB chunks for faster resumable upload
        )

        # Step 5: Create insert request
        logger.debug("[YouTube] Creating insert request...")
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=metadata,
            media_body=media,
        )

        # Step 6: Execute upload with resumable media and retry logic
        logger.info(f"[YouTube] Starting upload: {title[:50]}...")
        response = None
        attempt = 0
        max_attempts = 5

        while response is None and attempt < max_attempts:
            attempt += 1
            try:
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"[YouTube] Upload progress: {progress}% (attempt {attempt})")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:  # Transient errors
                    logger.warning(f"[YouTube] Transient error {e.resp.status}, retrying (attempt {attempt}/{max_attempts})...")
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise  # Non-transient error

        if response is None:
            logger.error(f"[FAIL] YouTube: Upload did not complete after {max_attempts} attempts")
            return None

        video_id = response.get("id", "")
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"[OK] Published to YouTube: {url}")
            logger.info(f"[YouTube] Video ID: {video_id} | Privacy: unlisted | Size: {video_size} bytes")
            return url

        logger.error("[FAIL] YouTube: No video_id in response")
        return None

    except HttpError as e:
        # Detailed error handling for YouTube API errors
        error_detail = ""
        if hasattr(e, "content"):
            try:
                error_detail = e.content.decode("utf-8")
            except Exception:
                error_detail = str(e)
        else:
            error_detail = str(e)

        logger.error(f"[FAIL] YouTube API error ({e.resp.status}): {error_detail[:500]}")

        # Log specific error codes
        if "dailyLimitExceeded" in error_detail:
            logger.error("[FAIL] YouTube: Daily upload quota exceeded. Try again tomorrow.")
        elif "quotaExceeded" in error_detail:
            logger.error("[FAIL] YouTube: Quota exceeded. Check API quota in Google Cloud Console.")
        elif "forbidden" in error_detail.lower():
            logger.error("[FAIL] YouTube: Access forbidden. Check YouTube channel and permissions.")

        return None

    except Exception as e:
        logger.error(f"[FAIL] YouTube: {type(e).__name__}: {str(e)}")
        import traceback
        logger.debug(f"[YouTube] Traceback: {traceback.format_exc()}")
        return None


# ── Publisher Registry ────────────────────────────────────────────────────────

SOCIAL_PUBLISHERS = {
    "twitter": publish_twitter,
    "reddit": publish_reddit,
    "linkedin": publish_linkedin,
    "facebook": publish_facebook,
    "instagram": publish_instagram,
    "tiktok": publish_tiktok,
    "youtube": publish_youtube,
}


def publish_to_all_platforms(
    article: Dict[str, Any],
    canonical_url: str,
    image_url: str = "",
    video_url: str = "",
    video_path: str = "",
) -> Dict[str, Optional[str]]:
    """
    Publish article to all configured social platforms simultaneously.

    Args:
        article: Article dict with keys: title, meta_description, body
        canonical_url: Full URL of published article (for text-based platforms)
        image_url: Public HTTPS URL of article image (for Instagram)
        video_url: Public HTTPS URL of article video (for TikTok)
        video_path: Local file path to .mp4 video (for YouTube upload)

    Returns:
        Dict[platform: url] mapping platform names to published post URLs (None if skipped/failed)

    Example:
        results = publish_to_all_platforms(
            article={
                "title": "10 Trading Strategies That Work",
                "meta_description": "Learn proven strategies...",
                "body": "Full article content here..."
            },
            canonical_url="https://profitengine.alreadyherellc.com/article",
            image_url="https://cdn.example.com/image.jpg",
            video_url="https://cdn.example.com/video.mp4",
            video_path="/tmp/article_video.mp4"
        )
        # {
        #   "twitter": "https://twitter.com/i/web/status/123456789",
        #   "reddit": "https://reddit.com/r/investing/comments/abc123/...",
        #   "linkedin": "https://www.linkedin.com/feed/update/urn:li:activity:1234567890",
        #   "facebook": "https://facebook.com/123456789_987654321",
        #   "instagram": None,  # Missing image_url
        #   "tiktok": None,     # Missing video_url
        #   "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        # }
    """
    results = {}

    for platform, publisher in SOCIAL_PUBLISHERS.items():
        try:
            if platform == "instagram":
                results[platform] = publisher(article, image_url)
            elif platform == "tiktok":
                results[platform] = publisher(article, video_url)
            elif platform == "youtube":
                results[platform] = publisher(article, video_path)
            else:
                results[platform] = publisher(article, canonical_url)
        except Exception as e:
            logger.error(f"[EXCEPTION] {platform}: {type(e).__name__}: {str(e)}")
            results[platform] = None

    return results


# ── Credential Setup & Rotation Guide ──────────────────────────────────────────

"""
CREDENTIAL SETUP AND ROTATION

All social media APIs use OAuth 2.0 or API keys for authentication.
Credentials are read from environment variables (never hardcoded in code).

Store all credentials in:
1. GitHub Secrets (for CI/CD)
2. OCI server .env file (runtime)
3. Vercel environment variables (Next.js frontend if needed)

TWITTER/X (OAuth 2.0)
  Credentials:
    - TWITTER_API_KEY (OAuth 2.0 Client ID)
    - TWITTER_API_SECRET (OAuth 2.0 Client Secret)
    - TWITTER_ACCESS_TOKEN (User access token)
    - TWITTER_ACCESS_SECRET (User access secret)
    - TWITTER_BEARER_TOKEN (v2 API Bearer Token) — preferred

  Setup:
    1. https://developer.twitter.com/en/portal/dashboard
    2. Create OAuth 2.0 2-legged app (or connect existing user)
    3. Copy credentials to env

  Rotation: Quarterly or after team changes

REDDIT (OAuth 2.0)
  Credentials:
    - REDDIT_CLIENT_ID (App Client ID)
    - REDDIT_CLIENT_SECRET (App Client Secret)
    - REDDIT_USERNAME (Bot account username)
    - REDDIT_PASSWORD (Bot account password)
    - REDDIT_SUBREDDIT (target subreddit, e.g. "investing")

  Setup:
    1. https://www.reddit.com/prefs/apps
    2. Create "script" app (not web app)
    3. Create separate bot account (username/password)
    4. Grant bot permissions to target subreddit

  Rotation: Quarterly or when changing subreddit

LINKEDIN (OAuth 2.0)
  Credentials:
    - LINKEDIN_ACCESS_TOKEN (OAuth 2.0 access token)
    - LINKEDIN_PERSON_URN (optional; if posting to personal profile)
    - LINKEDIN_ORGANIZATION_URN (optional; if posting to company page)

  Setup:
    1. https://www.linkedin.com/developers/apps
    2. Create new app (company context: Already Here LLC)
    3. Request Sign In with LinkedIn (user context) + Share on LinkedIn (pages)
    4. Generate access token via OAuth flow
    5. Get Person URN from /me endpoint or Company ID from company page

  Rotation: After 90 days (default LinkedIn token expiry) or sooner if compromised

FACEBOOK (Graph API)
  Credentials:
    - FB_PAGE_ID (Facebook page numeric ID)
    - FB_PAGE_ACCESS_TOKEN (Page access token with pages_manage_posts permission)

  Setup:
    1. https://developers.facebook.com/docs/pages/access-tokens
    2. Create app in Meta Business Suite
    3. Grant pages_manage_posts permission
    4. Generate long-lived page access token
    5. Copy page ID and token to env

  Rotation: Quarterly or after business account changes

INSTAGRAM (Graph API via Facebook)
  Credentials:
    - ig_user_id (Instagram Business Account ID)
    - FB_PAGE_ACCESS_TOKEN (Same as Facebook; requires instagram_content_publish)

  Setup:
    1. Convert personal Instagram account to business account
    2. Link to Facebook page via Meta Business Suite
    3. Generate Instagram Business Account ID
    4. Use same FB_PAGE_ACCESS_TOKEN as Facebook (with additional permissions)

  Requirements:
    - Must be Instagram Business Account (not Creator)
    - Must have image_url for each post (file upload not supported via API)
    - Captions limited to 2200 characters

  Rotation: Quarterly (same as Facebook)

TIKTOK (OAuth 2.0)
  Credentials:
    - TIKTOK_ACCESS_TOKEN (OAuth 2.0 access token)
    - TIKTOK_OPEN_ID (TikTok Business Account Open ID)

  Setup:
    1. https://developer.tiktok.com
    2. Create TikTok Business Account
    3. Create OAuth 2.0 app (video.upload scope)
    4. Generate access token via OAuth flow
    5. Get Open ID from TikTok Creator Center

  Requirements:
    - Business account only (personal accounts not supported by API)
    - Videos must be .mp4 or .mov, max 287MB
    - Requires video_url (remote upload) not local file upload

  Rotation: Quarterly or if Open ID changes

YOUTUBE (OAuth 2.0 with Refresh Token)
  Credentials:
    - YOUTUBE_CLIENT_ID (OAuth 2.0 Client ID)
    - YOUTUBE_CLIENT_SECRET (OAuth 2.0 Client Secret)
    - YOUTUBE_REFRESH_TOKEN (Refresh token for access token renewal)

  Setup:
    1. https://console.cloud.google.com/apis/credentials
    2. Create OAuth 2.0 Client ID (Desktop app)
    3. Download credentials.json
    4. Run initial OAuth flow to get refresh token
    5. Store YOUTUBE_REFRESH_TOKEN in env (safe for long-term storage)

  Requirements:
    - Google account with YouTube channel
    - youtube.upload scope
    - Requires video_path (local .mp4 file)

  Rotation: Refresh token valid indefinitely until revoked; rotate if compromised

SECURITY BEST PRACTICES
  1. Never commit credentials to git (use .env.example instead)
  2. Rotate credentials quarterly
  3. Use separate service accounts for testing vs. production
  4. Monitor API usage logs for suspicious activity
  5. Revoke old tokens immediately upon rotation
  6. Store credentials in locked environment (GitHub Secrets, OCI .env with 600 perms)
  7. Log all publishing attempts (successful and failed)
  8. Test with dry-run before enabling auto-publishing to production accounts

TROUBLESHOOTING

Twitter: Invalid credentials
  - Verify API Key/Secret vs. Bearer Token format
  - Check that app has Read+Write permissions
  - Confirm account not rate-limited (429 response)

Reddit: Invalid credentials
  - Verify bot account created and password correct
  - Check app type is "script" (not web app)
  - Confirm subreddit exists and bot has posting permissions

LinkedIn: 400 Bad Request
  - Verify Person URN format (urn:li:person:12345)
  - Check token has Sign In with LinkedIn + Share on LinkedIn scopes
  - Ensure post text under 3000 characters

Facebook: 400 Invalid token
  - Verify token is page access token (not user token)
  - Check token has pages_manage_posts permission
  - Confirm page ID is numeric (not page name)

Instagram: Container rejected
  - Verify image_url is public HTTPS (not local file)
  - Ensure image format is .jpg/.png (not .gif/.webp)
  - Check caption under 2200 characters

TikTok: 403 Forbidden
  - Verify account is TikTok Business Account (not personal)
  - Check TIKTOK_OPEN_ID is correct
  - Confirm video_url is publicly accessible

YouTube: 403 Forbidden
  - Verify refresh token not revoked (check Google Security Dashboard)
  - Confirm youtube.upload scope in OAuth consent
  - Check YouTube channel exists and is in good standing
"""
