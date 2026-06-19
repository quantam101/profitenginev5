# Content Engine Alternatives & Quality Enhancement

**Current Chain**: Groq (free credits) → HuggingFace (free) → Gemini  
**Goal**: Find better alternatives + build enhanced engine for eye-grabbing content

---

## Part 1: Better Provider Alternatives to HuggingFace

### Tier 1: FREE / Very Cheap (Best Value)

#### 1. **Together.ai** ⭐ RECOMMENDED
- **Quality**: High (access to Llama-70B, Mistral, Code-Llama)
- **Cost**: $0-10/mo with free credits
- **Speed**: Fast API
- **Limit**: 4M tokens/month free
- **Why Better**: Larger models (70B+) than HuggingFace (8B), better quality
- **Setup**: `pip install together`

```bash
# Get free credits at https://api.together.xyz/
TOGETHER_API_KEY=xxx python -c "
import together
together.api_key = 'xxx'
response = together.Complete.create(
    prompt='Write an article about...',
    model='meta-llama/Llama-2-70b-chat-hf',
    max_tokens=2000
)
"
```

#### 2. **Replicate** 
- **Quality**: Very High (Llama-70B, CodeLlama, custom fine-tuned)
- **Cost**: $0.00075/sec compute (~$2-3 per article)
- **Speed**: Slower (10-30 sec per request)
- **Limit**: Pay-as-you-go
- **Why Better**: Can run custom models, fine-tuned for your domain
- **Good For**: Premium content, one-off articles

```bash
# Get API key at https://replicate.com/
pip install replicate
export REPLICATE_API_TOKEN=xxx
```

#### 3. **OctoML / Optimized Inference**
- **Quality**: Good (quantized Llama-13B/70B)
- **Cost**: Cheap ($0.001-0.002 per request)
- **Speed**: Very fast
- **Why Better**: Optimized for inference speed/cost ratio
- **Setup**: https://octoml.ai

---

### Tier 2: QUALITY-FOCUSED (Pay for Better Results)

#### 4. **Claude API (Anthropic)**
- **Quality**: Excellent (best for long-form content)
- **Cost**: $0.003 input / $0.015 output per 1K tokens (~$0.10-0.50/article)
- **Speed**: Very fast
- **Why Use**: Best for nuanced, engaging, SEO-optimized content
- **Recommended Model**: `claude-3.5-sonnet` (best quality/cost)

```bash
pip install anthropic
export ANTHROPIC_API_KEY=xxx
```

#### 5. **GPT-4o (OpenAI)**
- **Quality**: Best (state-of-the-art)
- **Cost**: $0.015 input / $0.06 output per 1K (~$0.50-1.00/article)
- **Speed**: Fast
- **Why Use**: Best for premium, conversion-focused content
- **Recommended Model**: `gpt-4o-mini` (better value) or `gpt-4o` (best quality)

---

### Tier 3: CUSTOM/LOCAL (Maximum Control)

#### 6. **Local Ollama** (Run on OCI Server)
- **Quality**: Medium (Llama-2-13B locally)
- **Cost**: FREE (runs on your OCI machine)
- **Speed**: Slow (30-60 sec, depends on GPU)
- **Why Use**: No API calls, private data, zero dependencies
- **Setup**: Already in docker-compose.yml

```bash
# Already configured at http://ollama:11434
curl http://ollama:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Write an article about...",
  "stream": false
}'
```

#### 7. **LM Studio** (Desktop App)
- **Quality**: Good (run models locally)
- **Cost**: Free
- **Why Use**: Run on dev machine, test before production
- **Models**: Llama, Mistral, Phi, Code-Llama
- **Setup**: https://lmstudio.ai

---

## Part 2: Recommended Provider Strategy

### Phase 1: Current (Exploit Free Credits)
```
Groq (70B, free) → HuggingFace (8B, free) → Gemini
```
- ✅ Zero cost
- ✅ Fast
- ❌ Moderate quality

### Phase 2: Upgrade for Quality (Months 2-3)
```
Groq (when credits remain) 
→ Together.ai (70B, $0.10-0.20/article)
→ HuggingFace (fallback)
```
- ✅ Better quality than HuggingFace
- ✅ Cheap ($3-6/month)
- ✅ Larger models (70B)

### Phase 3: Premium Content (Months 4+)
```
Together.ai (for volume)
→ Claude-3.5-Sonnet (for premium articles, $0.10/article)
→ HuggingFace (fallback)
```
- ✅ Professional quality
- ✅ SEO-optimized
- ✅ Conversion-focused
- ~$30-50/month for daily publishing

---

## Part 3: Enhanced Content Engine for "Eye-Grabbing" Content

### Current Approach
- Single LLM call → Raw article → Publish

### Better Approach: Multi-Stage Refinement

#### Stage 1: Hook Generation (5-10 seconds)
Generate 3 different **opening hooks** for the same topic:
1. Data-driven hook ("Study shows...")
2. Story hook ("Imagine if...")
3. Contrarian hook ("Most people get this wrong...")

Pick the most engaging one.

```python
def generate_hooks(topic: str) -> List[str]:
    """Generate multiple article hooks"""
    hooks = []
    for approach in ["data", "story", "contrarian"]:
        prompt = f"Write a {approach} opening hook for: {topic}"
        hook = call_llm(prompt, max_tokens=100)
        hooks.append(hook)
    return hooks
```

#### Stage 2: Structure Optimization (SEO + Engagement)
Create a **skeleton** before full article:
```
1. Hook (most engaging from Stage 1)
2. Promise/Lead (what reader will learn)
3. 5-7 Section Headers (SEO keywords)
4. Callout/Stat placement
5. Conclusion + Call-to-Action
```

#### Stage 3: Full Article Generation
Generate with the optimized structure as context.

#### Stage 4: Engagement Enhancement
Post-process to add:
- 📊 Data points / statistics
- 🎯 Actionable takeaways (bullets)
- 💡 "Pro tips" callouts
- 🔗 Internal/affiliate links
- ❓ FAQ section

#### Stage 5: Optimization Check
Verify:
- ✅ Reading level (8th-grade for broad appeal)
- ✅ Keyword density (SEO)
- ✅ Readability (flesch score >60)
- ✅ Call-to-action present
- ✅ No jargon without explanation

---

## Part 4: Specific Eye-Grabbing Techniques

### What Makes Content "Eye-Grabbing"?

#### 1. **Hooks** (First 2 sentences)
❌ Bad: "This article discusses passive income strategies."  
✅ Good: "I made $10,000 last month without opening my laptop. Here's how."

#### 2. **Numbers & Data**
❌ Bad: "Many people want to earn more money."  
✅ Good: "87% of people want to earn passive income, but only 3% actually try."

#### 3. **Surprising Contrasts**
❌ Bad: "You can make money online."  
✅ Good: "Most online gurus are broke. Here's what actually works."

#### 4. **Format Variety**
- Lists (How to, Top 10, Mistakes)
- Step-by-step (Tutorial)
- Comparison (A vs B)
- Case study ("I did X, here's what happened")
- Question format ("Is X dead in 2026?")

#### 5. **Scannability**
- Short paragraphs (2-3 sentences max)
- Subheadings every 200 words
- Bullet points for lists
- **Bold** key phrases
- Pull quotes for stats

#### 6. **Emotion + Logic**
- Hook: Emotion (fear, curiosity, desire)
- Body: Logic (proof, data, steps)
- Close: Action (what to do next)

---

## Part 5: Implementation Options

### Option A: Quick Win (1-2 hours)
Add Together.ai as second provider:
```python
# Add to providers after Groq
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not groq_result and TOGETHER_API_KEY:
    result = call_together_api(prompt)
```

### Option B: Medium Enhancement (4-6 hours)
Implement multi-stage content engine:
1. Hook generation
2. Structure optimization
3. Full article
4. Post-processing

### Option C: Premium Build (1-2 days)
Full pipeline:
1. Multi-hook generation
2. Topic research (trending, related topics)
3. SEO keyword integration
4. Engagement scoring
5. A/B testing framework

---

## Part 6: Quick Implementation: Add Together.ai

### Step 1: Get Free Credits
1. Go to https://api.together.xyz/
2. Sign up (GitHub login)
3. Copy API key

### Step 2: Add to GitHub Secrets
```bash
gh secret set TOGETHER_API_KEY --body 'YOUR_KEY'
```

### Step 3: Update Code
Add this to `publish_article.py`:

```python
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY", "").strip()
TOGETHER_BASE = "https://api.together.xyz/v1"

def _call_together(prompt: str, model: str = "meta-llama/Llama-2-70b-chat-hf") -> str:
    import httpx
    response = httpx.post(
        f"{TOGETHER_BASE}/completions",
        headers={"Authorization": f"Bearer {TOGETHER_KEY}"},
        json={"prompt": prompt, "model": model, "max_tokens": 2048}
    )
    if response.status_code == 200:
        return response.json()["output"][0]["text"]
    raise Exception(f"Together API error: {response.text}")
```

Then update provider chain:
```python
if GROQ_KEY:
    # Try Groq
    raw = _call_groq(prompt)
elif TOGETHER_KEY:
    # Fallback to Together (better than HF)
    raw = _call_together(prompt)
elif HF_TOKEN:
    # Final fallback to HF
    raw = _call_hf_inference(prompt)
```

---

## Summary

| Provider | Quality | Cost/Article | Setup Time |
|----------|---------|--------------|-----------|
| **Groq** | High (70B) | Free | Done ✓ |
| **HuggingFace** | Medium (8B) | Free | Done ✓ |
| **Together.ai** | High (70B) | $0.10-0.20 | 15 min ⭐ |
| **Claude-3.5** | Very High | $0.10-0.50 | 20 min |
| **GPT-4o** | Best | $0.50-1.00 | 20 min |
| **Ollama (Local)** | Medium (13B) | Free | Done |

---

## Recommendation

**Next 48 hours:**
1. ✅ Use Groq + HuggingFace (current setup)
2. ✅ Add Together.ai ($3-6 budget for testing)
3. Test quality of all 3
4. Pick best, scale to that

**By Week 2:**
- If publishing daily: Together.ai is worth it ($6/mo vs HF quality)
- If doing premium content: Add Claude for special articles
- Keep HuggingFace as final fallback

**Estimated Cost/Month:**
- Free tier: $0
- Quality tier: $6-10 (Together.ai)
- Premium tier: $30-50 (Together + Claude mix)

Want me to implement Together.ai integration now?
