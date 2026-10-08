# ruff: noqa: S310
"""
EAOS Social Engine — Multi-platform posting with offline SQLite cache.
Platforms: X/Twitter (OAuth 1.0a), LinkedIn, Reddit, TikTok, Telegram,
           Facebook Pages, Instagram (Graph API), YouTube.
Falls back to local journal if network is down; auto-retries on restore.
"""
import os
import json
import hmac
import time
import base64
import sqlite3
import hashlib
import asyncio
import logging
import urllib.request
import urllib.error


def _urlopen_json(req: urllib.request.Request, timeout: int = 30) -> dict:
    """urlopen + json, preserving the API's real error body on failure."""
    try:
        raw = urllib.request.urlopen(req, timeout=timeout).read()
        return json.loads(raw) if raw.strip() else {"ok": True}
    except urllib.error.HTTPError as e:
        try:
            body = e.read()[:400].decode("utf-8", "replace")
        except Exception:
            body = ""
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


import urllib.parse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("EAOS.SocialEngine")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

DB_PATH = os.environ.get("EAOS_SOCIAL_DB", "./datacenter/social_cache.db")

_INVISIBLE_JUNK = str.maketrans("", "", "\ufeff\ufffe\u200b\u200c\u200d\u2060")


def _sanitize(text: str) -> str:
    """Strip BOM and zero-width characters that break platform APIs."""
    return text.translate(_INVISIBLE_JUNK).strip()


@dataclass
class SocialPost:
    db_id: Optional[int]
    platform: str
    text_content: str
    media_path: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class LocalPostJournal:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_queue (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform    TEXT NOT NULL,
                    text_content TEXT,
                    media_path  TEXT,
                    extra       TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def cache(self, post: SocialPost) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO pending_queue (platform, text_content, media_path, extra) VALUES (?, ?, ?, ?)",
                (post.platform, post.text_content, post.media_path, json.dumps(post.extra or {})),
            )
            conn.commit()
        logger.warning(f"[{post.platform}] Offline — post cached in local journal")

    def fetch_backlog(self) -> List[SocialPost]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, platform, text_content, media_path, extra FROM pending_queue ORDER BY id ASC"
            ).fetchall()
        return [SocialPost(r[0], r[1], r[2], r[3], json.loads(r[4] or "{}")) for r in rows]

    def clear(self, post_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM pending_queue WHERE id=?", (post_id,))
            conn.commit()


# ── Twitter OAuth 1.0a ─────────────────────────────────────────────────────

def _twitter_auth_header(method: str, url: str, params: Dict) -> str:
    api_key        = os.environ.get("TWITTER_API_KEY", "")
    api_secret     = os.environ.get("TWITTER_API_SECRET", "")
    access_token   = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    access_secret  = os.environ.get("TWITTER_ACCESS_SECRET", "")
    if not all([api_key, api_secret, access_token, access_secret]):
        return ""
    nonce = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    ts    = str(int(time.time()))
    oauth = {
        "oauth_consumer_key":     api_key,
        "oauth_nonce":            nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp":        ts,
        "oauth_token":            access_token,
        "oauth_version":          "1.0",
    }
    all_params = {**params, **oauth}
    param_str  = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
                          for k, v in sorted(all_params.items()))
    base_str   = "&".join([method.upper(), urllib.parse.quote(url, safe=""), urllib.parse.quote(param_str, safe="")])
    sign_key   = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_secret, safe='')}"
    sig        = base64.b64encode(hmac.new(sign_key.encode(), base_str.encode(), hashlib.sha1).digest()).decode()
    oauth["oauth_signature"] = sig
    header = "OAuth " + ", ".join(f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
                                   for k, v in sorted(oauth.items()))
    return header


async def _post_twitter(post: SocialPost) -> Optional[bool]:
    api_key = os.environ.get("TWITTER_API_KEY", "")
    if not api_key:
        logger.info("[Twitter] No credentials — skip")
        return None
    url    = "https://api.twitter.com/2/tweets"
    body   = json.dumps({"text": post.text_content[:280]}).encode()
    header = _twitter_auth_header("POST", url, {})
    if not header:
        return None
    try:
        req = urllib.request.Request(url, data=body, method="POST",
            headers={"Authorization": header, "Content-Type": "application/json"})
        data = _urlopen_json(req, timeout=15)
        tweet_id = data.get("data", {}).get("id", "")
        logger.info(f"[Twitter] Posted tweet id={tweet_id}")

        # Post thread replies if extra contains thread_tweets
        thread = (post.extra or {}).get("thread_tweets", [])
        reply_to = tweet_id
        for tweet_text in thread[1:]:
            time.sleep(1)
            t_body = json.dumps({"text": _sanitize(tweet_text)[:280], "reply": {"in_reply_to_tweet_id": reply_to}}).encode()
            t_header = _twitter_auth_header("POST", url, {})
            t_req = urllib.request.Request(url, data=t_body, method="POST",
                headers={"Authorization": t_header, "Content-Type": "application/json"})
            reply_to = _urlopen_json(t_req, timeout=15).get("data", {}).get("id", reply_to)
        return True
    except Exception as exc:
        logger.error(f"[Twitter] Post failed: {exc}")
        return False


# ── LinkedIn ───────────────────────────────────────────────────────────────

async def _post_linkedin(post: SocialPost) -> Optional[bool]:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    urn   = os.environ.get("LINKEDIN_PERSON_URN", "")
    if not token or not urn:
        logger.info("[LinkedIn] No credentials — skip")
        return None
    url  = "https://api.linkedin.com/v2/ugcPosts"
    body = json.dumps({
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post.text_content[:3000]},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }).encode()
    try:
        req = urllib.request.Request(url, data=body, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                     "X-Restli-Protocol-Version": "2.0.0"})
        _urlopen_json(req, timeout=15)
        logger.info("[LinkedIn] Posted")
        return True
    except Exception as exc:
        logger.error(f"[LinkedIn] Post failed: {exc}")
        return False


# ── Pinterest ─────────────────────────────────────────────────────────────

async def _post_pinterest(post: SocialPost) -> Optional[bool]:
    token = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
    board = os.environ.get("PINTEREST_BOARD_ID", "")
    if not token or not board:
        logger.info("[Pinterest] No credentials — skip")
        return None
    extra = post.extra or {}
    link  = extra.get("url", "")
    image = extra.get("image_url", "")
    body = {
        "board_id": board,
        "title": post.text_content[:100],
        "description": (extra.get("description") or post.text_content)[:500],
    }
    if link:
        body["link"] = link
    if image:
        body["media_source"] = {"source_type": "image_url", "url": image}
    else:
        # Pins require media — without an image URL this post is undeliverable.
        logger.info("[Pinterest] no image_url — skip")
        return None
    try:
        req = urllib.request.Request("https://api.pinterest.com/v5/pins",
            data=json.dumps(body).encode(), method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        data = _urlopen_json(req, timeout=15)
        logger.info(f"[Pinterest] Pin created id={data.get('id','')}")
        return True
    except Exception as exc:
        logger.error(f"[Pinterest] Post failed: {exc}")
        return False


# ── Reddit ─────────────────────────────────────────────────────────────────

async def _post_reddit(post: SocialPost) -> Optional[bool]:
    client_id     = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    username      = os.environ.get("REDDIT_USERNAME", "")
    password      = os.environ.get("REDDIT_PASSWORD", "")
    subreddit     = (post.extra or {}).get("subreddit", "passive_income")
    if not all([client_id, client_secret, username, password]):
        logger.info("[Reddit] No credentials — skip")
        return None
    try:
        # OAuth
        creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        auth_req = urllib.request.Request(
            "https://www.reddit.com/api/v1/access_token",
            data=urllib.parse.urlencode({
                "grant_type": "password", "username": username, "password": password
            }).encode(),
            headers={"Authorization": f"Basic {creds}", "User-Agent": "ProfitEngine/5.0"},
            method="POST",
        )
        token = _urlopen_json(auth_req, timeout=10).get("access_token", "")
        if not token:
            return False
        # Submit link/text post
        url   = (post.extra or {}).get("url", "")
        pdata = {
            "sr": subreddit, "kind": "link" if url else "self",
            "title": post.text_content[:300],
            "url": url, "resubmit": "true", "nsfw": "false",
        }
        submit_req = urllib.request.Request(
            "https://oauth.reddit.com/api/submit",
            data=urllib.parse.urlencode(pdata).encode(),
            headers={"Authorization": f"bearer {token}", "User-Agent": "ProfitEngine/5.0"},
            method="POST",
        )
        _urlopen_json(submit_req, timeout=15)
        logger.info(f"[Reddit] r/{subreddit} post submitted")
        return True
    except Exception as exc:
        logger.error(f"[Reddit] Post failed: {exc}")
        return False


# ── Telegram ───────────────────────────────────────────────────────────────

async def _post_telegram(post: SocialPost) -> Optional[bool]:
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.info("[Telegram] No credentials — skip")
        return None
    try:
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({"chat_id": chat_id, "text": post.text_content[:4096],
                           "parse_mode": "HTML", "disable_web_page_preview": False}).encode()
        req  = urllib.request.Request(url, data=body, method="POST",
            headers={"Content-Type": "application/json"})
        _urlopen_json(req, timeout=10)
        logger.info("[Telegram] Message sent")
        return True
    except Exception as exc:
        logger.error(f"[Telegram] Failed: {exc}")
        return False


# ── TikTok ─────────────────────────────────────────────────────────────────

async def _post_tiktok(post: SocialPost) -> Optional[bool]:
    token = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        logger.info("[TikTok] No credentials — skip")
        return None
    if not post.media_path or not os.path.exists(post.media_path):
        logger.info("[TikTok] No video file — skip")
        return None
    logger.info(f"[TikTok] Uploading {post.media_path} (TikTok upload API)")
    # TikTok Content Posting API v2
    try:
        url  = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        body = json.dumps({"post_info": {"title": post.text_content[:150],
                                          "privacy_level": "PUBLIC_TO_EVERYONE",
                                          "disable_duet": False, "disable_stitch": False,
                                          "disable_comment": False},
                           "source_info": {"source": "FILE_UPLOAD", "video_size": os.path.getsize(post.media_path),
                                            "chunk_size": os.path.getsize(post.media_path), "total_chunk_count": 1}}).encode()
        req  = urllib.request.Request(url, data=body, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"})
        data = _urlopen_json(req, timeout=15)
        upload_url = data.get("data", {}).get("upload_url", "")
        if not upload_url:
            return False
        with open(post.media_path, "rb") as vf:
            video_bytes = vf.read()
        upload_req = urllib.request.Request(upload_url, data=video_bytes, method="PUT",
            headers={"Content-Type": "video/mp4",
                     "Content-Range": f"bytes 0-{len(video_bytes)-1}/{len(video_bytes)}"})
        _urlopen_json(upload_req, timeout=120)
        logger.info("[TikTok] Video uploaded successfully")
        return True
    except Exception as exc:
        logger.error(f"[TikTok] Upload failed: {exc}")
        return False


# ── Facebook Pages ────────────────────────────────────────────────────────
async def _post_facebook(post: SocialPost) -> Optional[bool]:
    page_id    = os.environ.get("FB_PAGE_ID", "")
    page_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
    if not page_id or not page_token:
        logger.info("[Facebook] No credentials - skip")
        return None
    try:
        message = post.text_content[:2000]
        extra   = post.extra or {}
        payload: Dict[str, Any] = {"message": message, "access_token": page_token}
        if extra.get("url"):
            payload["link"] = extra["url"]
        body = urllib.parse.urlencode(payload).encode()
        req  = urllib.request.Request(
            f"https://graph.facebook.com/v21.0/{page_id}/feed",
            data=body, method="POST")
        resp = _urlopen_json(req, timeout=15)
        logger.info(f"[Facebook] Posted: {resp.get('id','?')}")
        return True
    except Exception as exc:
        logger.error(f"[Facebook] Post failed: {exc}")
        return False


# ── Instagram (Graph API) ──────────────────────────────────────────────────
async def _post_instagram(post: SocialPost) -> Optional[bool]:
    ig_user_id = os.environ.get("IG_USER_ID", "")
    page_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
    if not ig_user_id or not page_token:
        logger.info("[Instagram] No credentials - skip")
        return None
    try:
        extra   = post.extra or {}
        caption = post.text_content[:2200]
        base    = "https://graph.facebook.com/v21.0"

        # Pre-probe: proves the token can even see this IG account, so a
        # later 400 is known to be a media/permission issue, not auth.
        probe = urllib.request.Request(
            f"{base}/{ig_user_id}?fields=id,username,account_type&access_token={page_token}")
        try:
            account = _urlopen_json(probe, timeout=15)
        except Exception as probe_exc:
            # _urlopen_json raises on HTTP errors — a stale/misconfigured
            # IG_USER_ID lands here, so fall through to Page-based recovery.
            logger.info(f"[Instagram] account probe raised ({probe_exc}) — "
                        "attempting recovery via FB_PAGE_ID")
            account = {"error": True}
        if account.get("error") and os.environ.get("FB_PAGE_ID"):
            # IG_USER_ID misconfigured (Page ID set instead): resolve the
            # real instagram_business_account attached to the Page.
            resolved = _urlopen_json(urllib.request.Request(
                f"{base}/{os.environ['FB_PAGE_ID']}"
                f"?fields=instagram_business_account{{id,username,account_type}}"
                f"&access_token={page_token}"), timeout=15)
            real = (resolved.get("instagram_business_account") or {}).get("id")
            if real:
                logger.info(f"[Instagram] IG_USER_ID invalid — resolved {real} "
                            f"via page {os.environ['FB_PAGE_ID']}")
                ig_user_id = str(real)
                account = resolved.get("instagram_business_account") or {}
        logger.info(f"[Instagram] acting as @{account.get('username','?')}"
                    f" ({account.get('account_type','?')})")
        if account.get("account_type") not in ("BUSINESS", "CREATOR", None):
            logger.error("[Instagram] Account is not Business/Creator — "
                         "media publishing is not permitted on personal accounts")
            return False

        if post.media_path and post.media_path.endswith(".mp4"):
            # Reel upload
            params = urllib.parse.urlencode({
                "media_type": "REELS",
                "video_url": extra.get("video_url", ""),
                "caption": caption,
                "access_token": page_token,
            }).encode()
            req  = urllib.request.Request(f"{base}/{ig_user_id}/media", data=params, method="POST")
            data = _urlopen_json(req, timeout=30)
        else:
            # Image post — use a hosted image URL or skip
            img_url = extra.get("image_url", "")
            if not img_url:
                logger.info("[Instagram] No image_url provided — skipping")
                return False
            params = urllib.parse.urlencode({
                "image_url": img_url,
                "caption": caption,
                "access_token": page_token,
            }).encode()
            req  = urllib.request.Request(f"{base}/{ig_user_id}/media", data=params, method="POST")
            data = _urlopen_json(req, timeout=30)

        creation_id = data.get("id", "")
        if not creation_id:
            return False
        # Publish the container
        pub_params = urllib.parse.urlencode({
            "creation_id": creation_id,
            "access_token": page_token,
        }).encode()
        pub_req = urllib.request.Request(f"{base}/{ig_user_id}/media_publish",
                                          data=pub_params, method="POST")
        pub_data = _urlopen_json(pub_req, timeout=30)
        logger.info(f"[Instagram] Published: {pub_data.get('id','?')}")
        return True
    except Exception as exc:
        logger.error(f"[Instagram] Post failed: {exc}")
        return False


# ── YouTube ────────────────────────────────────────────────────────────────
async def _post_youtube(post: SocialPost) -> Optional[bool]:
    client_id     = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
    if not all([client_id, client_secret, refresh_token]):
        logger.info("[YouTube] No credentials - skip")
        return None
    if not post.media_path or not os.path.exists(post.media_path):
        logger.info("[YouTube] No video file — skipping")
        return None
    try:
        # Refresh access token
        token_body = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode()
        token_req  = urllib.request.Request("https://oauth2.googleapis.com/token",
                                             data=token_body, method="POST",
                                             headers={"Content-Type": "application/x-www-form-urlencoded"})
        token_data = _urlopen_json(token_req, timeout=15)
        access_token = token_data.get("access_token", "")
        if not access_token:
            logger.error("[YouTube] Failed to refresh access token")
            return False

        extra = post.extra or {}
        metadata = json.dumps({
            "snippet": {
                "title": post.text_content[:100],
                "description": _sanitize(extra.get("description", post.text_content[:5000])),
                "tags": extra.get("tags", ["ProfitEngine", "PassiveIncome", "AI", "AlreadyHereLLC"]),
                "categoryId": "28",  # Science & Technology
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        }).encode()

        # Resumable upload
        init_req = urllib.request.Request(
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            data=metadata, method="POST",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "video/mp4",
                "X-Upload-Content-Length": str(os.path.getsize(post.media_path)),
            })
        with urllib.request.urlopen(init_req, timeout=15) as r:
            upload_url = r.headers.get("Location", "")

        if not upload_url:
            logger.error("[YouTube] No upload URL received")
            return False

        with open(post.media_path, "rb") as vf:
            video_bytes = vf.read()
        upload_req = urllib.request.Request(upload_url, data=video_bytes, method="PUT",
            headers={"Content-Type": "video/mp4",
                     "Content-Length": str(len(video_bytes)),
                     "Authorization": f"Bearer {access_token}"})
        result = _urlopen_json(upload_req, timeout=300)
        video_id = result.get("id", "")
        logger.info(f"[YouTube] Uploaded: https://youtube.com/watch?v={video_id}")
        return True
    except Exception as exc:
        logger.error(f"[YouTube] Upload failed: {exc}")
        return False


# ── Main Engine ────────────────────────────────────────────────────────────

class ProductionSocialEngine:
    def __init__(self):
        self.journal = LocalPostJournal()

    async def _is_online(self) -> bool:
        try:
            urllib.request.urlopen("https://api.github.com", timeout=5)
            return True
        except Exception:
            return False

    async def publish(self, post: SocialPost) -> None:
        post.text_content = _sanitize(post.text_content)
        dispatch = {
            "X":         _post_twitter,
            "TWITTER":   _post_twitter,
            "LINKEDIN":  _post_linkedin,
            "REDDIT":    _post_reddit,
            "TELEGRAM":  _post_telegram,
            "TIKTOK":    _post_tiktok,
            "PINTEREST": _post_pinterest,
            "FACEBOOK":  _post_facebook,
            "INSTAGRAM": _post_instagram,
            "YOUTUBE":   _post_youtube,
        }
        fn = dispatch.get(post.platform.upper())
        if not fn:
            logger.warning(f"Unknown platform: {post.platform}")
            return
        if not await self._is_online():
            self.journal.cache(post)
            return
        ok = await fn(post)
        if ok and post.db_id:
            self.journal.clear(post.db_id)
        elif ok is False and not post.db_id:
            self.journal.cache(post)

    async def publish_all_platforms(self, text: str, url: str, tags: List[str],
                                     thread_tweets: Optional[List[str]] = None,
                                     video_path: Optional[str] = None) -> None:
        """Blast one piece of content to ALL configured platforms at once."""
        hashtags = " ".join(f"#{t.replace(' ', '')}" for t in (tags or [])[:5])
        telegram_msg = f"📝 <b>{text[:200]}</b>\n\n🔗 {url}\n\n{hashtags}"
        linkedin_msg = f"{text[:600]}\n\n{url}\n\n{hashtags}"
        reddit_title = text[:300]

        fb_msg  = f"{text[:600]}\n\n{url}\n\n{hashtags}"
        yt_desc = f"{text}\n\n{url}\n\n{hashtags}\n\nAlready Here LLC — AI-powered automation for small business."

        platform_posts = [
            SocialPost(None, "TELEGRAM", telegram_msg),
            SocialPost(None, "LINKEDIN", linkedin_msg),
            SocialPost(None, "FACEBOOK", fb_msg, extra={"url": url}),
            SocialPost(None, "REDDIT",   reddit_title, extra={"url": url, "subreddit": "passive_income"}),
            SocialPost(None, "INSTAGRAM", f"{text[:200]}\n\n{hashtags}",
                       extra={"url": url, "image_url": "https://quantam101.github.io/content/assets/og.png"}),
            SocialPost(None, "PINTEREST", text[:100],
                       extra={"url": url, "description": text[:500],
                              "image_url": "https://quantam101.github.io/content/assets/og.png"}),
        ]
        if thread_tweets:
            platform_posts.append(SocialPost(None, "X", thread_tweets[0],
                                              extra={"thread_tweets": thread_tweets}))
        if video_path:
            platform_posts.append(SocialPost(None, "TIKTOK", text[:150], media_path=video_path))
            platform_posts.append(SocialPost(None, "YOUTUBE", text[:100], media_path=video_path,
                                              extra={"description": yt_desc,
                                                     "tags": [t.replace("-","") for t in (tags or [])[:8]] +
                                                              ["ProfitEngine","PassiveIncome","AI","AlreadyHereLLC"]}))

        await asyncio.gather(*[self.publish(p) for p in platform_posts])

    async def run_sync_daemon(self) -> None:
        logger.info("[SocialEngine] Sync daemon active — monitoring offline journal")
        while True:
            await asyncio.sleep(30.0)
            backlog = self.journal.fetch_backlog()
            if not backlog or not await self._is_online():
                continue
            logger.info(f"[SocialEngine] Draining {len(backlog)} cached posts")
            for post in backlog:
                await self.publish(post)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = ProductionSocialEngine()
    logger.info("Social Engine online.")
