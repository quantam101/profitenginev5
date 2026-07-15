# The $0 Content Engine

### How a one-person company automates Shorts, Reels, and newsletters without paying for a single tool

*By Already Here LLC — the team behind @alreadyherellc*

---

## Why this exists

Most "content automation" advice ends with a $300/month software stack. This playbook is different: every tool in it is free, every step actually runs in production at our company today, and nothing here requires you to show your face, hire an editor, or buy credits.

This is the exact system we use to publish short-form video to YouTube, Instagram, and Facebook on autopilot — trend research included.

---

## Chapter 1 — The engine at a glance

One pipeline, five stages, zero dollars:

1. **Mine** — find what's already winning in your niches (views-per-day, not raw views)
2. **Design** — turn each winning topic into a script brief automatically
3. **Render** — voiceover, captions, B-roll, and music assembled by code
4. **Publish** — auto-post to YouTube Shorts, Instagram Reels, and Facebook
5. **Recycle** — repost your own best performers on a schedule

Each stage is a small script. Each script fails soft: if one breaks, the rest keep running. That's the whole architecture secret — no orchestration platform, no Zapier bill.

## Chapter 2 — Mine what's already winning

Don't guess topics. YouTube tells you what works if you rank search results by **views per day** instead of total views. A 2-year-old video with 1.8M views (~800/day) is a proven evergreen topic; a week-old video with 50k views (~7,000/day) is a rising trend. You want both.

The free tool: `yt-dlp` — it reads video metadata (title, views, upload date) from a search query with no API key. Twenty lines of Python turn "ai tools shorts" into a ranked list of topics your audience already rewards.

**The compliance rule that keeps your account alive:** mine the *topic*, never the video. Re-uploading someone else's clip earns copyright strikes. Recreating the topic with your own script and licensed footage is just publishing.

## Chapter 3 — Scripts that write themselves

Two layers, so it never breaks:

- **Layer 1 — free AI.** Several providers offer free tiers (Gemini, Groq, OpenRouter's free models). Chain them: try one, fall through to the next. Your prompt asks for a 55-word spoken script: hook → substance → call to action.
- **Layer 2 — templates.** When every API is down or you have zero keys, a template engine assembles the script from a topic's benefit list. Hooks like "Nobody tells you this about X" never expire.

Give each video a **format**: tips (numbered list), secrets (insider tone), story (struggle → discovery → payoff), DIY (three steps), or sales. Matching format to topic is worth more than any single "viral hook."

## Chapter 4 — Studio-grade rendering, free

- **Voiceover:** Microsoft Edge's `edge-tts` — neural voices, word-level timestamps, free, no account.
- **Captions:** those word timestamps become perfectly synced, word-by-word captions (the "CapCut look") rendered by ffmpeg.
- **B-roll:** Pexels' API is free and the footage is licensed for commercial use. Search by your topic keywords, cut every few seconds, add a transition and a swoosh.
- **Assembly:** ffmpeg does everything — 1080×1920, captions burned in, music ducked under the voice.

Render time per video: about a minute. Cost: $0.

## Chapter 5 — Publish everywhere, automatically

- **YouTube Shorts:** the Data API uploads directly. One OAuth setup, then it's hands-free.
- **Instagram Reels + Facebook:** Meta's Graph API posts video from any public URL. The gotcha nobody documents: Instagram's newer tokens only work against `graph.instagram.com`, not `graph.facebook.com`. Route by token prefix and both generations work.
- **Hosting the video file:** a public GitHub release is a free, stable URL that Instagram will happily fetch.

Schedule the whole pipeline in GitHub Actions (also free). Ours runs every Sunday at 2am and posts before we wake up.

## Chapter 6 — The recycle loop

Your own back catalog is free inventory. Once a video is 2+ weeks old, its performance is knowable: repost the winner with a fresh caption ("ICYMI:", "Still true:"). Mark reposts so you never repost a repost. One script, scheduled weekly, compounds your best work forever.

## Chapter 7 — The numbers that matter

- Views-per-day beats total views for topic selection
- 55 words ≈ 20 seconds — the retention sweet spot for Shorts
- 3 concrete tips beat 10 vague ones, every time
- Post consistently for 30 days before judging anything

---

## Steal this stack

Everything above, itemized: `yt-dlp` (trend data) · free-tier LLMs (scripts) · `edge-tts` (voice) · Pexels (footage) · `ffmpeg` (assembly) · YouTube Data API + Meta Graph API (publishing) · GitHub Actions + Releases (scheduling + hosting). Total monthly cost: **$0.**

**Want the running system instead of the parts list?** Follow **@alreadyherellc** on Instagram for the daily build-in-public version — or reach us at dispatch@alreadyherellc.com.

*© 2026 Already Here LLC. You're welcome to share this guide with attribution. Nothing here is legal advice; platform policies change — read them.*
