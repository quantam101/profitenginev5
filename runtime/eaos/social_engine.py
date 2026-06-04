"""
EAOS Social Engine — Multi-platform posting with offline SQLite cache.
Platforms: X/Twitter (OAuth 1.0a), LinkedIn, Reddit, TikTok, Telegram.
Falls back to local journal if network is down; auto-retries on restore.
"""
import os
import sys
import json
import hmac
import time
import base64
import sqlite3
import hashlib
import asyncio
import logging
import urllib.request
import urllib.parse
import urllib.error
import urllib.error
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("EAOS.SocialEngine")

DB_PATH = os.environ.get("EAOS_SOCIAL_DB", "./datacenter/social_cache.db")


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


async def _post_twitter(post: SocialPost) -> bool:
    api_key = os.environ.get("TWITTER_API_KEY", "")
    if not api_key:
        logger.info("[Twitter] No credentials — skip")
        return False
    url    = "https://api.twitter.com/2/tweets"
    body   = json.dumps({"text": post.text_content[:280]}).encode()
    header = _twitter_auth_header("POST", url, {})
    if not header:
        return False
    try:
        req = urllib.request.Request(url, data=body, method="POST",
            headers={"Authorization": header, "Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        tweet_id = data.get("data", {}).get("id", "")
        logger.info(f"[Twitter] Posted tweet id={tweet_id}")

        # Post thread replies if extra contains thread_tweets
        thread = (post.extra or {}).get("thread_tweets", [])
        reply_to = tweet_id
        for tweet_text in thread[1:]:
            time.sleep(1)
            t_body = json.dumps({"text": tweet_text[:280], "reply": {"in_reply_to_tweet_id": reply_to}}).encode()
            t_header = _twitter_auth_header("POST", url, {})
            t_req = urllib.request.Request(url, data=t_body, method="POST",
                headers={"Authorization": t_header, "Content-Type": "application/json"})
            t_resp = urllib.request.urlopen(t_req, timeout=15)
            reply_to = json.loads(t_resp.read()).get("data", {}).get("id", reply_to)
        return True
    except Exception as exc:
        logger.error(f"[Twitter] Post failed: {exc}")
        return False


# ── LinkedIn ───────────────────────────────────────────────────────────────

async def _post_linkedin(post: SocialPost) -> bool:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    urn   = os.environ.get("LINKEDIN_PERSON_URN", "")
    if not token or not urn:
        logger.info("[LinkedIn] No credentials — skip")
        return False
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
        resp = urllib.request.urlopen(req, timeout=15)
        logger.info(f"[LinkedIn] Posted — status {resp.status}")
        return True
    except Exception as exc:
        logger.error(f"[LinkedIn] Post failed: {exc}")
        return False


# ── Reddit ─────────────────────────────────────────────────────────────────

async def _post_reddit(post: SocialPost) -> bool:
    client_id     = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    username      = os.environ.get("REDDIT_USERNAME", "")
    password      = os.environ.get("REDDIT_PASSWORD", "")
    subreddit     = (post.extra or {}).get("subreddit", "passive_income")
    if not all([client_id, client_secret, username, password]):
        logger.info("[Reddit] No credentials — skip")
        return False
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
        token = json.loads(urllib.request.urlopen(auth_req, timeout=10).read()).get("access_token", "")
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
        resp = urllib.request.urlopen(submit_req, timeout=15)
        logger.info(f"[Reddit] r/{subreddit} post submitted")
        return True
    except Exception as exc:
        logger.error(f"[Reddit] Post failed: {exc}")
        return False


# ── Telegram ───────────────────────────────────────────────────────────────

async def _post_telegram(post: SocialPost) -> bool:
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.info("[Telegram] No credentials — skip")
        return False
    try:
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({"chat_id": chat_id, "text": post.text_content[:4096],
                           "parse_mode": "HTML", "disable_web_page_preview": False}).encode()
        req  = urllib.request.Request(url, data=body, method="POST",
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        logger.info("[Telegram] Message sent")
        return True
    except Exception as exc:
        logger.error(f"[Telegram] Failed: {exc}")
        return False


# ── TikTok ─────────────────────────────────────────────────────────────────

async def _post_tiktok(post: SocialPost) -> bool:
    token = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        logger.info("[TikTok] No credentials — skip")
        return False
    if not post.media_path or not os.path.exists(post.media_path):
        logger.info("[TikTok] No video file — skip")
        return False
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
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        upload_url = data.get("data", {}).get("upload_url", "")
        if not upload_url:
            return False
        with open(post.media_path, "rb") as vf:
            video_bytes = vf.read()
        upload_req = urllib.request.Request(upload_url, data=video_bytes, method="PUT",
            headers={"Content-Type": "video/mp4",
                     "Content-Range": f"bytes 0-{len(video_bytes)-1}/{len(video_bytes)}"})
        urllib.request.urlopen(upload_req, timeout=120)
        logger.info("[TikTok] Video uploaded successfully")
        return True
    except Exception as exc:
        logger.error(f"[TikTok] Upload failed: {exc}")
        return False


# ── Main Engine ────────────────────────────────────────────────────────────

class ProductionSocialEngine:
    def __init__(self):
        self.journal = LocalPostJournal()

    async def _is_online(self) -> bool:
        try:
            urllib.request.urlopen("https://1.1.1.1", timeout=3)
            return True
        except Exception:
            return False

    async def publish(self, post: SocialPost) -> None:
        if not await self._is_online():
            self.journal.cache(post)
            return
        dispatch = {
            "X":        _post_twitter,
            "TWITTER":  _post_twitter,
            "LINKEDIN": _post_linkedin,
            "REDDIT":   _post_reddit,
            "TELEGRAM": _post_telegram,
            "TIKTOK":   _post_tiktok,
        }
        fn = dispatch.get(post.platform.upper())
        if not fn:
            logger.warning(f"Unknown platform: {post.platform}")
            return
        ok = await fn(post)
        if ok and post.db_id:
            self.journal.clear(post.db_id)
        elif not ok and not post.db_id:
            self.journal.cache(post)

    async def publish_all_platforms(self, text: str, url: str, tags: List[str],
                                     thread_tweets: Optional[List[str]] = None,
                                     video_path: Optional[str] = None) -> None:
        """Blast one piece of content to ALL configured platforms at once."""
        hashtags = " ".join(f"#{t.replace(' ', '')}" for t in (tags or [])[:5])
        telegram_msg = f"📝 <b>{text[:200]}</b>\n\n🔗 {url}\n\n{hashtags}"
        linkedin_msg = f"{text[:600]}\n\n{url}\n\n{hashtags}"
        reddit_title = text[:300]

        platform_posts = [
            SocialPost(None, "TELEGRAM", telegram_msg),
            SocialPost(None, "LINKEDIN", linkedin_msg),
            SocialPost(None, "REDDIT",   reddit_title, extra={"url": url, "subreddit": "passive_income"}),
        ]
        if thread_tweets:
            platform_posts.append(SocialPost(None, "X", thread_tweets[0],
                                              extra={"thread_tweets": thread_tweets}))
        if video_path:
            platform_posts.append(SocialPost(None, "TIKTOK", text[:150], media_path=video_path))

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
