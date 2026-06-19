# LLM Fallback Cascade Implementation

## Overview
Successfully added OpenAI, OpenRouter, DeepSeek, and Anthropic (Claude) as cascading fallback providers to the content generation pipeline in `scripts/publish_article.py`.

## Cascade Chain
The provider fallback order is now:

1. **Groq** (Primary - free credits) → 4 models in rotation
   - `llama-3.3-70b-versatile` (env-configurable default)
   - `qwen-qwq-32b` (reasoning model)
   - `llama-3.1-8b-instant` (high quota)
   - `gemma2-9b-it` (alternative)

2. **HuggingFace** (Free serverless) → 3 models in rotation
   - `meta-llama/Llama-3.1-8B-Instruct`
   - `mistralai/Mistral-7B-Instruct-v0.3`
   - `microsoft/Phi-3-mini-4k-instruct`

3. **Gemini** (Google) 
   - `gemini-2.0-flash` (configurable)

4. **OpenAI** ← NEW
   - `gpt-4o-mini` (configurable)

5. **OpenRouter** ← NEW
   - `openai/gpt-4o-mini` (configurable)

6. **DeepSeek** ← NEW
   - `deepseek-chat` (configurable)

7. **Anthropic/Claude** ← NEW
   - `claude-3-5-sonnet-20241022` (configurable)

## Implementation Details

### Environment Variables Added
```bash
OPENAI_API_KEY                # from platform.openai.com/api-keys
OPENROUTER_API_KEY            # from openrouter.ai/keys
DEEPSEEK_API_KEY              # from platform.deepseek.com/api/keys
ANTHROPIC_API_KEY             # from console.anthropic.com/api/keys
```

### Model Configuration Variables (Optional)
```bash
OPENAI_MODEL="gpt-4o-mini"                      # Default: gpt-4o-mini
OPENROUTER_MODEL="openai/gpt-4o-mini"           # Default: openai/gpt-4o-mini
DEEPSEEK_MODEL="deepseek-chat"                  # Default: deepseek-chat
ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"   # Default: claude-3-5-sonnet-20241022
```

### New Functions Added

1. **`_call_openai(prompt: str) -> str`**
   - Calls OpenAI API endpoint: `https://api.openai.com/v1/chat/completions`
   - Uses Bearer token auth
   - Supports retry with exponential backoff

2. **`_call_openrouter(prompt: str) -> str`**
   - Calls OpenRouter API endpoint: `https://openrouter.ai/api/v1/chat/completions`
   - Uses Bearer token auth
   - Supports retry with exponential backoff

3. **`_call_deepseek(prompt: str) -> str`**
   - Calls DeepSeek API endpoint: `https://api.deepseek.com/chat/completions`
   - Uses Bearer token auth
   - Supports retry with exponential backoff

4. **`_call_anthropic(prompt: str) -> str`**
   - Calls Anthropic API endpoint: `https://api.anthropic.com/v1/messages`
   - Uses x-api-key header + Bearer token auth
   - Different response format: `response["content"][0]["text"]` instead of message.content
   - Supports retry with exponential backoff

### Enhanced `generate_article()` Function
- Now checks for all 7 LLM providers (instead of 3)
- Falls through cascade if any provider fails
- Each provider can have multiple models (Groq and HF)
- Comprehensive error messages show which provider failed and tries next
- If all providers exhaust, descriptive error message lists all configured providers

### Enhanced `_verify_ai_provider()` Function
- Now verifies all 6+ new LLM providers
- Reports which providers are reachable
- Returns True if at least ONE provider is configured and working
- Shows provider status breakdown in verification output

Example verification output:
```
[VERIFY][OK] Groq: API key accepted
[VERIFY][OK] HuggingFace: API key accepted
[VERIFY][OK] OpenAI: API key accepted (gpt-4o-mini)
[VERIFY][OK] OpenRouter: API key accepted (openai/gpt-4o-mini)
[VERIFY][OK] DeepSeek: API key accepted (deepseek-chat)
[VERIFY][OK] Anthropic: API key accepted (claude-3-5-sonnet-20241022)
[VERIFY][OK] AI providers: 6/6 providers reachable
```

## API Compatibility

All 6 new providers use standard OpenAI-compatible request/response formats where applicable:

| Provider | Chat Endpoint | Auth | Response Format |
|----------|---------------|------|-----------------|
| OpenAI | `/v1/chat/completions` | Bearer token | `choices[0].message.content` |
| OpenRouter | `/v1/chat/completions` | Bearer token | `choices[0].message.content` |
| DeepSeek | `/chat/completions` | Bearer token | `choices[0].message.content` |
| Anthropic | `/v1/messages` | x-api-key header | `content[0].text` |

## Testing & Verification

Run verification mode:
```bash
CONTENT_VERIFY_ONLY=true python scripts/publish_article.py
```

This tests credentials for all 6 providers without generating or publishing articles.

Generate article (uses cascade):
```bash
python scripts/publish_article.py
```

The script will try each provider in cascade order until one succeeds.

## Fallback Behavior

- If Groq quota is exhausted → tries all Groq models, then falls through to HF
- If HF limits hit → tries all HF models, then falls through to Gemini
- If Gemini fails → tries OpenAI
- If OpenAI fails → tries OpenRouter
- If OpenRouter fails → tries DeepSeek
- If DeepSeek fails → tries Anthropic (last resort)
- If all fail → exits with error listing all attempted providers

## Cost Implications

| Provider | Cost | Quota Status |
|----------|------|------|
| Groq | Free (credits) | 9,000 tokens/day (free tier) |
| HuggingFace | Free (serverless) | Generous free tier |
| Gemini | Free tier available | Limited but free |
| OpenAI | Paid | $0.15/1M input, $0.60/1M output tokens (gpt-4o-mini) |
| OpenRouter | Paid | Variable per model, but aggregated |
| DeepSeek | Paid | ~$0.14/1M tokens (cheaper than OpenAI) |
| Anthropic | Paid | $3/1M input, $15/1M output tokens (Claude 3.5) |

## Configuration for Production

1. Add all required API keys to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   OPENROUTER_API_KEY=sk-...
   DEEPSEEK_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-...
   ```

2. Add to GitHub Secrets for CI/CD:
   - `OPENAI_API_KEY`
   - `OPENROUTER_API_KEY`
   - `DEEPSEEK_API_KEY`
   - `ANTHROPIC_API_KEY`

3. Optional: Configure preferred models via env vars
   ```bash
   OPENAI_MODEL="gpt-4o"              # Upgrade to full model
   ANTHROPIC_MODEL="claude-3-opus-20250514"  # Upgrade to Opus
   ```

## Files Modified

- `scripts/publish_article.py` (main implementation)
  - Added 4 new provider functions
  - Updated `generate_article()` with cascade logic
  - Enhanced `_verify_ai_provider()` with 6-provider checks
  - Updated docstring with new env vars

## Success Criteria

✓ All 6 new LLM providers are wired into the cascade  
✓ Groq quota exhaustion triggers fallback chain  
✓ Cascade tries providers in documented priority order  
✓ Verification mode tests all 6 providers  
✓ All provider API keys are from credentials (not placeholder)  
✓ Error handling includes all providers in error message  
✓ No placeholder values or hardcoded test tokens  

## Notes

- Anthropic API uses different auth model (x-api-key header) than others
- OpenRouter acts as an aggregator for multiple models
- DeepSeek is significantly cheaper than OpenAI ($0.14 vs $0.75 per 1M tokens)
- All fallback providers use same system prompt and temperature (0.7) for consistency
- Max token output is 3000 for all providers (suitable for 800-1200 word articles)
