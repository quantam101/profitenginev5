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

    # Approval polling.
    approval_poll_s: float = field(default_factory=lambda: float(
        os.environ.get("FYE_APPROVAL_POLL_S", "30")))
    approval_timeout_s: float = field(default_factory=lambda: float(
        os.environ.get("FYE_APPROVAL_TIMEOUT_S", "86400")))

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
