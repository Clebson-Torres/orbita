"""Caminhos padrão e configurações do Orbita.

O diretório de dados fica em %APPDATA%\\Orbita — assim o .env,
memory.json e audit.log vivem num lugar fixo independente de onde
o usuário roda o comando.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir() -> Path:
    """Retorna %APPDATA%\\Orbita no Windows, ~/.orbita em outros sistemas."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Orbita"
    return Path.home() / ".orbita"


def default_env_file() -> Path:
    return default_data_dir() / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(default_env_file()), env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_user_id: int = Field(alias="TELEGRAM_ALLOWED_USER_ID")
    bot_default_backend: Literal["lmstudio", "ollama"] = Field(default="ollama", alias="BOT_DEFAULT_BACKEND")

    lmstudio_base_url: str = Field(default="http://127.0.0.1:1234", alias="LMSTUDIO_BASE_URL")
    lmstudio_api_token: str = Field(default="", alias="LMSTUDIO_API_TOKEN")
    lmstudio_model: str = Field(default="qwen3:4b", alias="LMSTUDIO_MODEL")
    lmstudio_mcp_mode: Literal["disabled", "plugin", "ephemeral"] = Field(
        default="plugin", alias="LMSTUDIO_MCP_MODE"
    )
    lmstudio_mcp_plugin_id: str = Field(default="mcp/windows-mcp", alias="LMSTUDIO_MCP_PLUGIN_ID")
    lmstudio_mcp_server_url: str = Field(default="", alias="LMSTUDIO_MCP_SERVER_URL")
    lmstudio_mcp_server_label: str = Field(default="windows-mcp", alias="LMSTUDIO_MCP_SERVER_LABEL")
    lmstudio_mcp_allowed_tools: str = Field(
        default="Snapshot,Click,Type,Scroll,Move,Shortcut,Wait", alias="LMSTUDIO_MCP_ALLOWED_TOOLS"
    )

    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen3:4b", alias="OLLAMA_MODEL")

    data_dir: str = Field(default_factory=lambda: str(default_data_dir()), alias="BOT_DATA_DIR")

    @property
    def allowed_mcp_tools(self) -> list[str]:
        return [t.strip() for t in self.lmstudio_mcp_allowed_tools.split(",") if t.strip()]

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def load_settings(env_file: str | Path | None = None) -> Settings:
    path = Path(env_file) if env_file else default_env_file()
    return Settings(_env_file=str(path))
