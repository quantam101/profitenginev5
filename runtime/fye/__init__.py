"""
FYE — Faceless YouTube Engine pipeline (master build doc v0.2.1).

One supervisor (`FyeOrchestrator`) runs one agent per pipeline process:
research → script → shots → stills → voiceover → assembly → compliance →
publish gate. Every gate decision is journaled (append-only, hash-chained)
and publish is gated on a human decision recorded in daily-command-os.

Honesty constraints baked in (per the build doc):
  - RPM values are US-weighted planning priors, never revenue promises.
  - Midjourney has no official API — not wired. Flux (Replicate) is the
    automated stills path when REPLICATE_API_TOKEN + paid adapters allow.
  - Runway/Pika are paid, API-gated, volatile — the shots agent emits a
    shot list for a human/operator instead of faking automation.
  - AI-generated content carries YouTube synthetic-media disclosure;
    publishing is always human-approved.
"""

from .config import FyeConfig
from .journal import DecisionJournal
from .orchestrator import FyeOrchestrator
from .rpm_priors import RPM_PRIORS, RpmPrior, ypp_gate

__all__ = [
    "FyeConfig",
    "FyeOrchestrator",
    "DecisionJournal",
    "RPM_PRIORS",
    "RpmPrior",
    "ypp_gate",
]
