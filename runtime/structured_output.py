"""
Structured Output — schema-enforced JSON extraction for agent responses.

Problem: every agent does its own ad-hoc JSON extraction:
    start = result.find("{")
    end   = result.rfind("}") + 1
    parsed = json.loads(result[start:end])

This is fragile and duplicates the same try/except pattern 8+ times.

This module replaces that pattern with a single, robust function that:
  1. Strips LLM preamble / markdown code fences
  2. Extracts the first complete JSON object or array
  3. Validates required keys (if schema provided)
  4. Returns a typed result with fallback semantics

Usage
-----
    from runtime.structured_output import extract_json, OutputResult

    result = extract_json(llm_output, required_keys=["title", "body"])
    if result.ok:
        article = result.data           # dict or list
    else:
        article = result.fallback       # caller-supplied default

Prompt Engineering Appendix
----------------------------
To maximise parse success, append this to any system prompt that needs JSON:

    RESPOND WITH VALID JSON ONLY. No preamble, no commentary, no markdown
    fences. Start your response with { or [ and end with } or ].

The constant OUTPUT_CONSTRAINT_JSON below is this exact string, ready to
concatenate onto any system prompt.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# ── prompt engineering constants ─────────────────────────────────────────────

OUTPUT_CONSTRAINT_JSON = (
    "\n\nRESPOND WITH VALID JSON ONLY. "
    "No preamble, no commentary, no markdown fences. "
    "Start your response with { or [ and end with } or ]."
)

OUTPUT_CONSTRAINT_CONCISE = (
    "\n\nBe maximally concise. "
    "No filler phrases like 'Sure, I can help' or 'Great question'. "
    "Respond directly."
)

OUTPUT_CONSTRAINT_CSV = (
    "\n\nRespond with comma-separated values only. No header row unless requested."
)


# ── result type ───────────────────────────────────────────────────────────────

@dataclass
class OutputResult:
    ok:       bool
    data:     Optional[Union[Dict, List]]
    raw:      str
    fallback: Optional[Union[Dict, List]] = field(default=None)
    error:    str = ""

    def get(self, key: str, default: Any = None) -> Any:
        """Convenience: safely get a key from data dict."""
        if self.ok and isinstance(self.data, dict):
            return self.data.get(key, default)
        return default


# ── extraction ────────────────────────────────────────────────────────────────

_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*([\s\S]*?)```")


def extract_json(
    text: str,
    required_keys: Optional[List[str]] = None,
    fallback: Optional[Union[Dict, List]] = None,
    allow_array: bool = True,
) -> OutputResult:
    """
    Extract and validate a JSON object (or array) from raw LLM output.

    Parameters
    ----------
    text          : Raw LLM response string.
    required_keys : If provided, extraction fails unless all keys are present
                    in the parsed dict (ignored for arrays).
    fallback      : Value to place in OutputResult.fallback on failure.
    allow_array   : If True, also accept a JSON array as top-level value.

    Returns
    -------
    OutputResult with .ok=True if a valid JSON structure was found.
    """
    # 1. Strip markdown fences — model may wrap JSON in ```json...```
    fence_match = _FENCE_RE.search(text)
    if fence_match:
        candidate = fence_match.group(1).strip()
        result = _try_parse(candidate, required_keys, allow_array)
        if result.ok:
            result.fallback = fallback
            return result

    # 2. Find first { or [ and last matching } or ]
    for opener, closer in [("{", "}"), ("[", "]")]:
        if not allow_array and opener == "[":
            continue
        start = text.find(opener)
        end   = text.rfind(closer)
        if start < 0 or end <= start:
            continue
        candidate = text[start : end + 1]
        result = _try_parse(candidate, required_keys, allow_array)
        if result.ok:
            result.fallback = fallback
            return result

    return OutputResult(ok=False, data=None, raw=text, fallback=fallback,
                        error="no_json_structure_found")


def _try_parse(
    candidate: str,
    required_keys: Optional[List[str]],
    allow_array: bool,
) -> OutputResult:
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return OutputResult(ok=False, data=None, raw=candidate,
                            error=f"json_decode_error: {exc}")

    if not isinstance(parsed, (dict, list)):
        return OutputResult(ok=False, data=None, raw=candidate,
                            error=f"unexpected_type: {type(parsed).__name__}")

    if isinstance(parsed, list) and not allow_array:
        return OutputResult(ok=False, data=None, raw=candidate,
                            error="array_not_allowed")

    if required_keys and isinstance(parsed, dict):
        missing = [k for k in required_keys if k not in parsed]
        if missing:
            return OutputResult(ok=False, data=None, raw=candidate,
                                error=f"missing_required_keys: {missing}")

    return OutputResult(ok=True, data=parsed, raw=candidate)


# ── key/value extraction for non-JSON outputs ─────────────────────────────────

def extract_key_value(text: str, key: str, default: str = "") -> str:
    """
    Extract a single value from LLM output of the form:
        Key: value
    Case-insensitive, returns default if not found.
    """
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+)$", re.I | re.M)
    m = pattern.search(text)
    return m.group(1).strip() if m else default


def extract_list(text: str, separator: str = r"[\n,;|]") -> List[str]:
    """
    Split a flat list from LLM output. Strips list-item markers (-, *, 1.).
    """
    items = re.split(separator, text)
    cleaned = []
    for item in items:
        item = re.sub(r"^\s*[-*\d.]+\s*", "", item).strip()
        if len(item) > 2:
            cleaned.append(item)
    return cleaned
