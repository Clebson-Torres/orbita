from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import httpx

from .telegram_api import TelegramAPI

LM_STUDIO_DOWNLOAD_URL = "https://lmstudio.ai/download"
WINDOWS_MCP_URL = "https://github.com/CursorTouch/Windows-MCP"
DEFAULT_LMSTUDIO_URL = "http://127.0.0.1:1234"
DEFAULT_WINDOWS_MCP_PLUGIN_ID = "mcp/windows-mcp"
DEFAULT_WINDOWS_MCP_LABEL = "windows-mcp"
DEFAULT_WINDOWS_MCP_TOOLS = ["Snapshot", "Click", "Type", "Scroll", "Move", "Shortcut", "Wait"]


def detect_python_status() -> dict[str, Any]:
    version = sys.version_info
    ok = version >= (3, 12)
    return {
        "name": "python",
        "ok": ok,
        "message": f"Python {version.major}.{version.minor}.{version.micro}",
    }


def detect_install_mode() -> str:
    current = Path(__file__).resolve()
    if (current.parents[2] / "pyproject.toml").exists():
        return "editable"
    return "installed"


def detect_lmstudio_installation() -> dict[str, Any]:
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "LM Studio" / "LM Studio.exe",
        Path("C:/Program Files/LM Studio/LM Studio.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return {"ok": True, "path": str(candidate)}
    return {"ok": False, "path": ""}


def get_lmstudio_mcp_config_path() -> Path:
    return Path.home() / ".lmstudio" / "mcp.json"


def has_uv() -> bool:
    return shutil.which("uv") is not None or shutil.which("uvx") is not None


def read_lmstudio_mcp_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else get_lmstudio_mcp_config_path()
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_windows_mcp_entry(path: str | Path | None = None, label: str = DEFAULT_WINDOWS_MCP_LABEL) -> Path:
    config_path = Path(path) if path else get_lmstudio_mcp_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = read_lmstudio_mcp_config(config_path)
    servers = payload.get("mcpServers", {})
    servers[label] = {
        "command": "uvx",
        "args": ["windows-mcp"],
    }
    payload["mcpServers"] = servers
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return config_path


async def validate_telegram_token(token: str) -> dict[str, Any]:
    api = TelegramAPI(token)
    try:
        return await api.get_me()
    finally:
        await api.close()


async def discover_telegram_user(token: str, timeout_seconds: int = 60) -> dict[str, Any] | None:
    api = TelegramAPI(token)
    try:
        return await api.wait_for_new_message(timeout_seconds=timeout_seconds, poll_interval_seconds=1)
    finally:
        await api.close()


async def probe_lmstudio(base_url: str, api_token: str = "") -> dict[str, Any]:
    headers: dict[str, str] = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{base_url.rstrip('/')}/api/v1/models", headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"name": "lmstudio", "ok": False, "message": f"LM Studio not reachable: {exc}", "models": []}

    payload = response.json()
    raw_models = payload.get("data") or payload.get("models") or []
    models: list[str] = []
    for item in raw_models:
        if isinstance(item, dict):
            model_id = item.get("id") or item.get("model_key") or item.get("identifier")
            if model_id:
                models.append(str(model_id))
        elif isinstance(item, str):
            models.append(item)

    return {
        "name": "lmstudio",
        "ok": True,
        "message": f"LM Studio online at {base_url}",
        "models": models,
    }


async def probe_ollama(base_url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"name": "ollama", "ok": False, "message": f"Ollama not reachable: {exc}"}
    return {"name": "ollama", "ok": True, "message": f"Ollama online at {base_url}"}


async def probe_windows_mcp(
    mode: str = "plugin", plugin_id: str = DEFAULT_WINDOWS_MCP_PLUGIN_ID, server_url: str = ""
) -> dict[str, Any]:
    if mode == "disabled":
        return {"name": "mcp", "ok": True, "message": "Windows-MCP disabled"}
    if mode == "ephemeral":
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(server_url)
                if response.status_code < 500:
                    return {"name": "mcp", "ok": True, "message": f"Windows-MCP reachable at {server_url}"}
            except httpx.HTTPError as exc:
                return {"name": "mcp", "ok": False, "message": f"Windows-MCP not reachable: {exc}"}
        return {"name": "mcp", "ok": False, "message": f"Windows-MCP endpoint failed: {server_url}"}

    config = read_lmstudio_mcp_config()
    servers = config.get("mcpServers", {})
    label = plugin_id.split("/", 1)[-1]
    if label in servers and has_uv():
        return {"name": "mcp", "ok": True, "message": f"Windows-MCP configured in {get_lmstudio_mcp_config_path()}"}
    if label in servers and not has_uv():
        return {"name": "mcp", "ok": False, "message": "Windows-MCP is configured but uv/uvx is not installed"}
    return {"name": "mcp", "ok": False, "message": "Windows-MCP plugin is not configured in LM Studio"}
