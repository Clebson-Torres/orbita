from __future__ import annotations

from pathlib import Path


ENV_ORDER = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_ALLOWED_USER_ID",
    "BOT_DEFAULT_BACKEND",
    "BOT_DATA_DIR",
    "LMSTUDIO_BASE_URL",
    "LMSTUDIO_API_TOKEN",
    "LMSTUDIO_MODEL",
    "LMSTUDIO_MCP_MODE",
    "LMSTUDIO_MCP_PLUGIN_ID",
    "LMSTUDIO_MCP_SERVER_URL",
    "LMSTUDIO_MCP_SERVER_LABEL",
    "LMSTUDIO_MCP_ALLOWED_TOOLS",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
]


class EnvFile:
    def __init__(self, path: str | Path = ".env") -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def read(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        values: dict[str, str] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def merge(self, updates: dict[str, str], preserve_existing: bool = True) -> dict[str, str]:
        values = self.read()
        for key, value in updates.items():
            if value == "":
                continue
            if preserve_existing and values.get(key):
                continue
            values[key] = value
        return values

    def write(self, values: dict[str, str]) -> None:
        ordered_keys = [key for key in ENV_ORDER if key in values]
        remaining_keys = sorted(key for key in values if key not in ENV_ORDER)
        lines = [f"{key}={values[key]}" for key in [*ordered_keys, *remaining_keys]]
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
