from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


@dataclass(slots=True)
class TelegramUpdate:
    update_id: int
    message: dict[str, Any] | None = None


class TelegramAPI:
    def __init__(self, bot_token: str, client: httpx.AsyncClient | None = None) -> None:
        self._bot_token = bot_token
        self._client = client or httpx.AsyncClient(timeout=60.0)

    @property
    def base_url(self) -> str:
        return f"https://api.telegram.org/bot{self._bot_token}"

    async def close(self) -> None:
        await self._client.aclose()

    async def get_me(self) -> dict[str, Any]:
        response = await self._client.get(f"{self.base_url}/getMe")
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram getMe failed: {payload}")
        return dict(payload["result"])

    async def get_updates(self, offset: int | None = None, timeout: int = 30) -> list[TelegramUpdate]:
        params: dict[str, Any] = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        response = await self._client.get(f"{self.base_url}/getUpdates", params=params)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram getUpdates failed: {payload}")
        return [
            TelegramUpdate(update_id=item["update_id"], message=item.get("message"))
            for item in payload.get("result", [])
        ]

    async def send_message(self, chat_id: int, text: str) -> None:
        payload = {"chat_id": chat_id, "text": text}
        response = await self._client.post(f"{self.base_url}/sendMessage", json=payload)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram sendMessage failed: {data}")

    async def send_photo(self, chat_id: int, photo_path: str | Path, caption: str = "") -> None:
        path = Path(photo_path)
        with path.open("rb") as photo_file:
            response = await self._client.post(
                f"{self.base_url}/sendPhoto",
                data={"chat_id": str(chat_id), "caption": caption},
                files={"photo": (path.name, photo_file, "image/png")},
            )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram sendPhoto failed: {data}")

    async def wait_for_new_message(
        self, timeout_seconds: int = 60, poll_interval_seconds: float = 2.0
    ) -> dict[str, Any] | None:
        existing = await self.get_updates(timeout=1)
        offset = max((update.update_id for update in existing), default=-1) + 1
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            remaining = max(1, int(deadline - time.monotonic()))
            updates = await self.get_updates(offset=offset, timeout=min(remaining, 10))
            for update in updates:
                offset = update.update_id + 1
                message = update.message or {}
                user = message.get("from") or {}
                chat = message.get("chat") or {}
                if "id" in user and "id" in chat:
                    return {
                        "user_id": int(user["id"]),
                        "chat_id": int(chat["id"]),
                        "username": user.get("username", ""),
                        "text": message.get("text", ""),
                    }
            if poll_interval_seconds > 0:
                await asyncio.sleep(poll_interval_seconds)
