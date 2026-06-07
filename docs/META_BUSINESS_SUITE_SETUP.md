# Meta Business Suite Publishing Setup

ProfitEngine can post to Facebook Pages and Instagram through `runtime/eaos/social_engine.py`.

## Required Info

Do not paste passwords or access tokens into chat. Add secrets in GitHub/Vercel/server env only.

1. Meta Business Portfolio name and business ID.
2. Facebook Page ID for the page you want to post to.
3. Instagram Professional account ID connected to that Facebook Page.
4. A Meta app with Graph API permissions approved or available for your account:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_basic`
   - `instagram_content_publish`
5. A long-lived Facebook Page access token for that Page.
6. Public image/video URLs for Instagram posts. Instagram Graph API cannot publish directly from a local file path.

## Environment Variables

Set these outside the repo:

```bash
FB_PAGE_ID=
FB_PAGE_ACCESS_TOKEN=
IG_USER_ID=
```

Optional queue/cache:

```bash
EAOS_SOCIAL_DB=./datacenter/social_cache.db
```

## Verify Without Posting

```bash
python scripts/meta_business_status.py
```

The checker confirms the Page and Instagram account are reachable with the supplied token.

## Notes

- Facebook text/link posts use `/{page_id}/feed`.
- Instagram posts use container creation plus `/media_publish`.
- For Instagram images, pass a hosted `image_url`.
- For Instagram reels/videos, pass a hosted `video_url`; local uploads are not enough for Graph publish.
- Keep posting permissions scoped to the exact business assets ProfitEngine should manage.
