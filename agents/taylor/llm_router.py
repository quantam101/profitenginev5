"""Multi-provider LLM failover status and routing metadata for Taylor."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class LLMState(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    FAILED = auto()


@dataclass
class LLMProvider:
    name: str
    provider: str
    model: str
    api_key_env: str
    endpoint: str
    cost_per_1k_tokens: float
    state: LLMState = field(default=LLMState.HEALTHY, init=False)
    fail_count: int = field(default=0, init=False)
    failed_at: float = field(default=0.0, init=False)

    @property
    def api_key(self) -> str:
        if self.provider == "ollama":
            return os.getenv(self.api_key_env, "ollama")
        return os.getenv(self.api_key_env, "")

    @property
    def available(self) -> bool:
        if self.state is LLMState.FAILED:
            return False
        if self.provider == "ollama":
            return bool(self.endpoint) and bool(self.api_key)
        return bool(self.api_key)


PROVIDERS = [
    LLMProvider("ollama-llama3.2", "ollama", "llama3.2", "OLLAMA_API_KEY", (os.environ.get("OLLAMA_BASE_URL") or "").strip(), 0.0),
    LLMProvider("deepseek-chat", "openai-compatible", "deepseek-chat", "DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", 0.00014),
    LLMProvider("gemini-flash", "google", "gemini-1.5-flash", "GOOGLE_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai", 0.000075),
    LLMProvider("claude-haiku", "anthropic", "claude-3-5-haiku-latest", "ANTHROPIC_API_KEY", "https://api.anthropic.com", 0.00025),
    LLMProvider("gpt-4o-mini", "openai", "gpt-4o-mini", "OPENAI_API_KEY", "https://api.openai.com/v1", 0.00015),
    LLMProvider("claude-sonnet", "anthropic", "claude-sonnet-4-20250514", "ANTHROPIC_API_KEY", "https://api.anthropic.com", 0.003),
    LLMProvider("gpt-4o", "openai", "gpt-4o", "OPENAI_API_KEY", "https://api.openai.com/v1", 0.005),
]


class LLMRouter:
    def __init__(self, recovery_seconds: float = 300.0) -> None:
        self.recovery_seconds = recovery_seconds

    def recover(self) -> None:
        now = time.monotonic()
        for provider in PROVIDERS:
            if provider.state is LLMState.FAILED and now - provider.failed_at >= self.recovery_seconds:
                provider.state = LLMState.HEALTHY
                provider.fail_count = 0
                provider.failed_at = 0.0

    def active_provider(self) -> Optional[LLMProvider]:
        self.recover()
        return next((provider for provider in PROVIDERS if provider.available), None)

    def status(self) -> list[dict[str, object]]:
        self.recover()
        return [
            {
                "name": provider.name,
                "provider": provider.provider,
                "model": provider.model,
                "state": provider.state.name,
                "key_set": bool(provider.api_key),
                "cost_per_1k_tokens": provider.cost_per_1k_tokens,
            }
            for provider in PROVIDERS
        ]

    def retell_config(self) -> dict[str, object]:
        provider = self.active_provider()
        if provider is None:
            raise RuntimeError("No Taylor LLM provider is configured")
        return {
            "provider": provider.provider,
            "model": provider.model,
            "base_url": provider.endpoint,
            "api_key_env": provider.api_key_env,
        }


_router = LLMRouter()


def get_router() -> LLMRouter:
    return _router


if __name__ == "__main__":
    router = get_router()
    print("Taylor LLM Failover Chain")
    print("-" * 72)
    for index, provider in enumerate(PROVIDERS, 1):
        key_state = "SET" if provider.api_key else "NOT SET"
        print(f"{index}. {provider.name:<18} provider={provider.provider:<18} key={key_state}")
    active = router.active_provider()
    print(f"\nActive provider: {active.name if active else 'NONE'}")
