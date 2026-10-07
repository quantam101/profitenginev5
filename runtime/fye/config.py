"""FYE configuration — env-driven, fail-closed, no placeholders."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FyeConfig:
    # Storage root for packages, journal, manifests.
    root: str = field(default_factory=lambda: os.environ.get(
        "FYE_ROOT", "./data/fye"))

    # Command OS (daily-command-os) wiring.
    dc_webhook_url: str = field(default_factory=lambda: os.environ.get(
        "DC_WEBHOOK_URL", "").strip())
    webhook_secret: str = field(default_factory=lambda: os.environ.get(
        "WEBHOOK_SECRET", "").strip())

    # Automated stills path: Flux on Replicate. Opt-in and gated on the
    # global paid-adapters flag — default is the zero-spend local renderer.
    replicate_token: str = field(default_factory=lambda: os.environ.get(
        "REPLICATE_API_TOKEN", "").strip())
    replicate_model: str = field(default_factory=lambda: os.environ.get(
        "FYE_FLUX_MODEL", "black-forest-labs/flux-schnell").strip())
    paid_adapters_enabled: bool = field(default_factory=lambda: os.environ.get(
        "GMAOS_PAID_ADAPTERS_ENABLED", "false").lower() == "true")

    # Free-tier stock B-roll sources (no cost, used before Flux/SVG).
    pexels_key: str = field(default_factory=lambda: os.environ.get(
        "PEXELS_API_KEY", "").strip())
    pixabay_key: str = field(default_factory=lambda: os.environ.get(
        "PIXABAY_API_KEY", "").strip())

    # Voiceover voice (edge-tts neural voice name).
    tts_voice: str = field(default_factory=lambda: os.environ.get(
        "FYE_TTS_VOICE", "").strip())

    # Approval polling.
    approval_poll_s: float = field(default_factory=lambda: float(
        os.environ.get("FYE_APPROVAL_POLL_S", "30")))
    approval_timeout_s: float = field(default_factory=lambda: float(
        os.environ.get("FYE_APPROVAL_TIMEOUT_S", "86400")))

    # Dispatch credential: fine-grained GitHub token (or App installation
    # token) scoped to Actions:write on this repo ONLY. No broad repo PAT.
    dispatch_token: str = field(default_factory=lambda: os.environ.get(
        "FYE_DISPATCH_TOKEN", "").strip())
    dispatch_repo: str = field(default_factory=lambda: os.environ.get(
        "FYE_DISPATCH_REPO", "quantam101/profitenginev5").strip())
    dispatch_workflow: str = field(default_factory=lambda: os.environ.get(
        "FYE_DISPATCH_WORKFLOW", "fye-run.yml").strip())
    dispatch_ref: str = field(default_factory=lambda: os.environ.get(
        "FYE_DISPATCH_REF", "main").strip())

    # Resource controls — keep the Actions worker from becoming the same
    # cost/runtime problem the Render box was.
    job_ttl_s: float = field(default_factory=lambda: float(
        os.environ.get("FYE_JOB_TTL_S", "86400")))
    render_timeout_s: float = field(default_factory=lambda: float(
        os.environ.get("FYE_RENDER_TIMEOUT_S", "1200")))
    max_artifact_bytes: int = field(default_factory=lambda: int(
        os.environ.get("FYE_MAX_ARTIFACT_MB", "500")) * 1024 * 1024)
    max_attempts: int = field(default_factory=lambda: int(
        os.environ.get("FYE_MAX_ATTEMPTS", "3")))

    @property
    def dc_base_url(self) -> str:
        """Base URL of daily-command-os derived from the webhook URL."""
        url = self.dc_webhook_url
        suffix = "/api/events/webhook"
        if url.endswith(suffix):
            return url[: -len(suffix)]
        return url.rstrip("/")

    @property
    def dc_configured(self) -> bool:
        return bool(self.dc_webhook_url and self.webhook_secret)

    @property
    def replicate_enabled(self) -> bool:
        return bool(self.replicate_token) and self.paid_adapters_enabled

    @property
    def broll_enabled(self) -> bool:
        return bool(self.pexels_key or self.pixabay_key)
