"""
backend/services/content_generation_service.py — ProfitEngine v5.0
Script/content generation service backed by the LLM failover chain.
Mirrors agents/content/index.js logic in Python.
"""
from content_models import ContentScript
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging
from services.distillation_service import distill_text, to_yaml_payload
from services.llm_runner import run_cached, llm_complete
import hashlib
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from .llm_runner import llm_complete
MIN_WORD_COUNT = int(os.environ.get('MIN_WORD_COUNT', '600'))
MAX_WORD_COUNT = int(os.environ.get('MAX_WORD_COUNT', '2000'))
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'alreadyherellc.com')
CONTENT_TYPES = ['how-to guide', 'listicle', 'case study', 'product review', 'comparison post', 'ultimate guide']

@dataclass
class ContentScript:
    id: str
    slug: str
    title: str
    content_type: str
    niche: Optional[str]
    keywords: list[str]
    body: str
    word_count: int
    generated_at: str
    published: bool
    metadata: dict[str, Any]

def _title_hash(title: str) -> str:
    return hashlib.sha256(title.encode()).hexdigest()[:12]

def _slugify(title: str) -> str:
    return re.sub('^-|-$', '', re.sub('[^a-z0-9]+', '-', title.lower()))

def _word_count(text: str) -> int:
    return len(text.split())

def _build_prompt(idea: str, content_type: str, niche: Optional[str]=None) -> str:
    niche_str = niche or 'general'
    return f'''Write a comprehensive {content_type} blog post optimized for SEO, reader engagement, and affiliate revenue.\n\nTopic: "{idea}"\nNiche: {niche_str}\nAngle: practical guide for beginners\n\nRequirements:\n- {MIN_WORD_COUNT}-{MAX_WORD_COUNT} words\n- Compelling H1 title (different from topic if needed)\n- SEO-optimized H2/H3 subheadings\n- Natural affiliate mentions with [AMAZON_LINK] placeholder\n- Engaging hook in first 2 sentences\n- Expert-level insights (not generic)\n- Concrete examples and data points\n- Clear action steps in each section\n- Strong CTA at end\n\nFrontmatter required:\n---\ntitle: [compelling SEO title]\ndescription: [150-char meta description]\ntags: [comma list]\ndate: {time.strftime('%Y-%m-%d')}\nniche: {niche_str}\n---'''

def _quality_gate(body: str, title: str) -> bool:
    wc = _word_count(body)
    if wc < MIN_WORD_COUNT:
        return False
    if '##' not in body:
        return False
    return True

async def generate_script_from_idea(idea: dict, db=None) -> ContentScript:
    """
    Generate a content script from an idea using AI.
    Uses Emergent LLM key with Gemini for zero-cost generation.

    Runs through the unified llm_runner so:
      - Identical idea prompts hit the cache and skip the LLM call
      - Tokens consumed are tracked in the daily budget collection
      - Daily cap (LLM_DAILY_TOKEN_CAP) is enforced
    """
    prompt = create_script_prompt(idea)
    system_msg = 'You are an expert content creator specializing in viral short-form and long-form content. Create engaging, high-converting scripts.'
    try:
        response = await llm_complete(system=system_msg, user=prompt, max_tokens=1000, session_id=f"script_gen_{idea['id']}")
    except Exception as e:
        logger.warning('script gen via llm_complete failed: %s', e)
        return create_fallback_script(idea, str(e))
    parsed = parse_script_response(response)
    return ContentScript(idea_id=idea['id'], hook=parsed['hook'], script_body=parsed['script_body'], cta=parsed['cta'], duration_seconds=60, shot_list=parsed['shot_list'], metadata={'generated_by': 'ai', 'model': 'gemini-3-flash'})

def _extract_section(line: str) -> tuple[str | None, str]:
    """Return (section_name, content) if line starts with a known marker, else (None, '')."""
    for marker, name in SECTION_MARKERS.items():
        if line.startswith(marker):
            return (name, line.replace(marker, '').strip())
    return (None, '')

def parse_script_response(response: str) -> dict:
    """Parse AI response into script components."""
    sections = {'hook': '', 'script_body': '', 'cta': '', 'shot_list': []}
    current_section = None
    for line in response.split('\n'):
        section_name, content = _extract_section(line)
        if section_name:
            current_section = section_name
            if section_name == 'shots':
                sections['shot_list'] = [s.strip() for s in content.split(',') if s.strip()]
            elif section_name == 'script':
                sections['script_body'] = content
            else:
                sections[section_name] = content
        elif current_section == 'script' and line.strip():
            sections['script_body'] += ' ' + line.strip()
    return {'hook': sections['hook'] or DEFAULT_HOOK, 'script_body': sections['script_body'] or response, 'cta': sections['cta'] or DEFAULT_CTA, 'shot_list': sections['shot_list'] or DEFAULT_SHOTS}

def create_script_prompt(idea: dict) -> str:
    """Create the AI prompt for script generation.

    Uses YAML for the idea payload (token-cheaper than embedding fields inline
    in prose) and applies semantic compression to the wrapper text.
    """
    payload = to_yaml_payload({'title': idea.get('title', ''), 'description': idea.get('description', ''), 'topic': idea.get('topic', ''), 'platforms': idea.get('target_platforms', [])})
    raw = f'Create a compelling content script for this idea.\n\nIDEA (YAML):\n{payload}\n\nProduce:\n1. Hook (first 3 seconds, stop-the-scroll)\n2. Script body (engaging, concise, value-driven)\n3. CTA (call to action)\n4. Shot list (5-7 visual scenes)\n\nFormat exactly:\nHOOK: [hook text]\nSCRIPT: [script body]\nCTA: [call to action]\nSHOTS: [shot 1], [shot 2], [shot 3], ...\n'
    return distill_text(raw)

def create_fallback_script(idea: dict, error: str) -> ContentScript:
    """Create a template script when AI generation fails."""
    return ContentScript(idea_id=idea['id'], hook=f"Discover the secret to {idea['title']}", script_body=f"{idea['description']}\n\n[AI generation temporarily unavailable: {error}]\n\nThis is a template script. Edit to customize.", cta='Follow for more valuable content!', duration_seconds=60, shot_list=['Opening hook', 'Main point 1', 'Main point 2', 'Proof/example', 'Call to action'], metadata={'generated_by': 'template', 'error': error})

async def generate_captions_for_platform(script: dict, platform: str) -> str:
    """Generate platform-specific captions with hashtags."""
    platform_limits = {'tiktok': 2200, 'youtube_shorts': 100, 'instagram': 2200, 'twitter': 280, 'linkedin': 3000}
    max_length = platform_limits.get(platform, 2000)
    caption = f"{script['hook']}\n\n{script['script_body'][:max_length - 200]}\n\n{script['cta']}"
    return caption

def get_base_hashtags(topic: str) -> list:
    """Generate base hashtags for any topic."""
    return [f"#{topic.replace(' ', '')}", '#content', '#viral', '#fyp', '#trending']

def get_platform_hashtags(platform: str) -> list:
    """Get platform-specific hashtags."""
    platform_tags = {'tiktok': ['#tiktok', '#foryou', '#foryoupage'], 'instagram': ['#instagram', '#reels', '#instagood'], 'youtube': ['#youtube', '#shorts', '#viral'], 'twitter': ['#twitter', '#thread'], 'linkedin': ['#linkedin', '#professional', '#business']}
    return platform_tags.get(platform, [])

async def generate_hashtags(topic: str, platform: str) -> list:
    """Generate relevant hashtags for the topic and platform."""
    base_tags = get_base_hashtags(topic)
    platform_tags = get_platform_hashtags(platform)
    tags = base_tags + platform_tags
    return tags[:10]
