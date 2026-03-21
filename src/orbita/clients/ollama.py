from __future__ import annotations

from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str, model: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client or httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def chat(self, prompt: str) -> str:
        body: dict[str, Any] = {
            "model": self._model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = await self._client.post(f"{self._base_url}/api/chat", json=body)
        response.raise_for_status()
        payload = response.json()
        message = payload.get("message", {})
        content = message.get("content", "")
        if not content:
            raise RuntimeError(f"Ollama response did not contain content: {payload}")
        return str(content).strip()

