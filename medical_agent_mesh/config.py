from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    ollama_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
    database_path: Path = Path(os.getenv("MEDICAL_MESH_DB", "data/medical-agent-mesh.sqlite3"))
    source_file: Path = Path(os.getenv("MEDICAL_MESH_SOURCE", "data/medical-opportunities.json"))
    timezone: str = os.getenv("MEDICAL_MESH_TIMEZONE", "America/Phoenix")
    sam_api_key: str | None = os.getenv("SAM_GOV_API_KEY")
    network_enabled: bool = _bool("MEDICAL_MESH_NETWORK_ENABLED", False)
    allow_outreach_send: bool = _bool("MEDICAL_MESH_ALLOW_SEND", False)
    company_auto_liability: int = int(os.getenv("COMPANY_AUTO_LIABILITY_USD", "0"))
    company_cargo_coverage: int = int(os.getenv("COMPANY_CARGO_COVERAGE_USD", "0"))
    driver_hipaa: bool = _bool("DRIVER_HIPAA_CERTIFIED", False)
    driver_bbp: bool = _bool("DRIVER_BBP_CERTIFIED", False)

    def validate(self) -> None:
        if not self.ollama_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("OLLAMA_BASE_URL must remain loopback-only for the local mesh")
        if self.network_enabled and not self.sam_api_key:
            raise ValueError("SAM_GOV_API_KEY is required when network retrieval is enabled")

