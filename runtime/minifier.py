"""
ManifestMinifier — fast, deterministic prompt compression.

This module provides two levels of compression:

  Level 1 (original): strip markdown fences + collapse whitespace.
  Level 2 (enhanced): full distillation pipeline (noise_strip + dedup).

The SovereignAutomationCore uses this on system_declaration + dynamic_context
before any caching or routing decisions.

Using distillation here (before the vector cache lookup) means:
  • Cache vectors are computed on clean, normalised text → better hit rates
  • Fewer tokens reach the inference tier regardless of cache outcome
"""
from __future__ import annotations

import re
from typing import Tuple

from .distillation import noise_strip, dedup_sentences, estimate_tokens


class ManifestMinifier:
    """
    Two-stage compressor for system declarations and dynamic context.

    Stage A — structural: strip markdown, collapse whitespace (fast, always on)
    Stage B — semantic:   noise_strip + sentence dedup (optional, ~2-5 ms)
    """

    MARKDOWN_FENCES = re.compile(r"```[a-zA-Z0-9_-]*|```")
    MULTISPACE      = re.compile(r"\s+")

    def minify(
        self,
        system_declaration: str,
        dynamic_context: str,
        deep: bool = True,
    ) -> Tuple[str, str]:
        """
        Clean both halves of the manifest.

        Parameters
        ----------
        system_declaration : The agent's system prompt.
        dynamic_context    : Runtime context / task background.
        deep               : If True (default), also run noise_strip + dedup
                             on dynamic_context (system prompts are already
                             concise and shouldn't be aggressively stripped).

        Returns
        -------
        (clean_system, clean_context)
        """
        clean_system  = self._structural(system_declaration)
        clean_context = self._structural(dynamic_context)

        if deep and clean_context:
            clean_context = dedup_sentences(noise_strip(clean_context))

        return clean_system, clean_context

    def _structural(self, value: str) -> str:
        """Strip markdown fences and collapse whitespace."""
        value = self.MARKDOWN_FENCES.sub("", value)
        value = " ".join(line.strip() for line in value.splitlines() if line.strip())
        value = self.MULTISPACE.sub(" ", value)
        return value.strip()

    def token_count(self, system: str, context: str) -> int:
        """Rough token estimate for the combined manifest."""
        return estimate_tokens(system + context)
