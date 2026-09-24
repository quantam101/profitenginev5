from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 180) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def healthcheck(self) -> None:
        try:
            with urlopen(f"{self.base_url}/api/tags", timeout=5) as response:  # noqa: S310
                if response.status != 200:
                    raise RuntimeError(f"Ollama healthcheck returned HTTP {response.status}")
        except URLError as exc:
            raise RuntimeError("Ollama is not reachable on the configured loopback URL") from exc

    def generate_json(self, system: str, prompt: str, schema: dict) -> dict:
        payload = json.dumps({
            "model": self.model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0.2, "num_ctx": 8192},
        }).encode()
        request = Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})  # noqa: S310
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                result = json.load(response)
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("Local Ollama generation failed") from exc
        return json.loads(result["response"])

