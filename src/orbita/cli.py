"""CLI do Orbita.

Comandos disponíveis:
    orbita setup              — wizard interativo de configuração inicial
    orbita run                — inicia o bot
    orbita doctor             — verifica se tudo está configurado
    orbita env                — exibe o .env atual (com mascaramento)
    orbita skills             — lista as skills disponíveis na pasta skills/
    orbita check telegram     — testa só o token do Telegram
    orbita check lmstudio     — testa só o LM Studio
    orbita check mcp          — testa só o Windows-MCP
    orbita check ollama       — testa só o Ollama

O .env e os dados de runtime ficam em %APPDATA%\\Orbita por padrão.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

import typer

from .config import default_data_dir, default_env_file
from .diagnostics import (
    DEFAULT_LMSTUDIO_URL,
    DEFAULT_WINDOWS_MCP_LABEL,
    DEFAULT_WINDOWS_MCP_PLUGIN_ID,
    DEFAULT_WINDOWS_MCP_TOOLS,
    LM_STUDIO_DOWNLOAD_URL,
    WINDOWS_MCP_URL,
    detect_install_mode,
    detect_lmstudio_installation,
    detect_python_status,
    discover_telegram_user as discover_telegram_user_async,
    has_uv,
    probe_lmstudio as probe_lmstudio_async,
    probe_ollama as probe_ollama_async,
    probe_windows_mcp as probe_windows_mcp_async,
    validate_telegram_token as validate_telegram_token_async,
    write_windows_mcp_entry,
)
from .env_file import EnvFile
from .main import run_bot
from .skills import SkillRegistry

app = typer.Typer(
    no_args_is_help=True,
    help="Orbita — controle seu PC Windows via Telegram com LLM local.",
)
check_app = typer.Typer(no_args_is_help=True, help="Verificações individuais de integração.")
app.add_typer(check_app, name="check")

SECRET_KEYS = {"TELEGRAM_BOT_TOKEN", "LMSTUDIO_API_TOKEN"}
RISK_ICON = {"read": "🟢", "write": "🟡", "exec": "🔴"}
DEFAULT_RECOMMENDED_LMSTUDIO_MODEL = "qwen3:4b"

# Padrão fixo — resolve na primeira chamada para garantir que APPDATA já está disponível
def _default_env() -> Path:
    return default_env_file()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _run(coro):
    return asyncio.run(coro)


def _mask(key: str, value: str) -> str:
    if key not in SECRET_KEYS:
        return value
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:4]}***{value[-2:]}"


def _ok(result: dict[str, Any]) -> None:
    state = "OK  " if result.get("ok") else "FAIL"
    typer.echo(f"  {state} {result.get('name', '?'):12s} {result.get('message', '')}")


def _section(title: str) -> None:
    typer.echo(f"\n{'─' * 50}")
    typer.echo(f"  {title}")
    typer.echo(f"{'─' * 50}")


def _open_url(url: str, label: str) -> None:
    if typer.confirm(f"Abrir {label} no browser?", default=True):
        webbrowser.open(url)


def _maybe_install_uv() -> None:
    if has_uv():
        return
    typer.echo("  uv/uvx não encontrado. O Windows-MCP usa uvx.")
    if typer.confirm("  Instalar uv com pip agora?", default=False):
        subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=False)


def _choose_model(default: str, models: list[str]) -> str:
    if not models:
        recommended = default or DEFAULT_RECOMMENDED_LMSTUDIO_MODEL
        typer.echo("  Nenhum modelo carregado no LM Studio.")
        typer.echo(f"  Recomendado para comecar: {recommended}")
        typer.echo("  Se tiver mais memoria disponivel, qwen3:8b costuma ser um bom passo seguinte.")
        typer.echo("  Carregue um modelo no LM Studio ou informe o nome manualmente para continuar.")
        return typer.prompt("  Modelo", default=recommended)
    typer.echo("  Modelos detectados no LM Studio:")
    for i, m in enumerate(models, 1):
        typer.echo(f"    {i}. {m}")
    best_default = default if default in models else models[0]
    return typer.prompt("  Modelo a usar", default=best_default)


# ------------------------------------------------------------------
# Probes síncronos
# ------------------------------------------------------------------

def probe_lmstudio(base_url: str, api_token: str = "") -> dict[str, Any]:
    return _run(probe_lmstudio_async(base_url, api_token))


def probe_windows_mcp(
    mode: str = "plugin",
    plugin_id: str = DEFAULT_WINDOWS_MCP_PLUGIN_ID,
    server_url: str = "",
) -> dict[str, Any]:
    return _run(probe_windows_mcp_async(mode=mode, plugin_id=plugin_id, server_url=server_url))


def probe_ollama(base_url: str) -> dict[str, Any]:
    return _run(probe_ollama_async(base_url))


def _full_doctor(values: dict[str, str]) -> list[dict[str, Any]]:
    token = values.get("TELEGRAM_BOT_TOKEN", "")
    if token:
        try:
            identity = _run(validate_telegram_token_async(token))
            tg = {"name": "telegram", "ok": True, "message": f"@{identity.get('username', '?')} válido"}
        except Exception as exc:
            tg = {"name": "telegram", "ok": False, "message": str(exc)}
    else:
        tg = {"name": "telegram", "ok": False, "message": "Token não configurado"}

    return [
        detect_python_status(),
        tg,
        probe_lmstudio(
            values.get("LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_URL),
            values.get("LMSTUDIO_API_TOKEN", ""),
        ),
        probe_windows_mcp(
            mode=values.get("LMSTUDIO_MCP_MODE", "plugin"),
            plugin_id=values.get("LMSTUDIO_MCP_PLUGIN_ID", DEFAULT_WINDOWS_MCP_PLUGIN_ID),
            server_url=values.get("LMSTUDIO_MCP_SERVER_URL", ""),
        ),
        probe_ollama(values.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")),
    ]


# ------------------------------------------------------------------
# setup
# ------------------------------------------------------------------

@app.command()
def setup(
    env_file: Path = typer.Option(
        None,
        help="Caminho do .env. Padrão: %APPDATA%\\Orbita\\.env",
        exists=False, dir_okay=False, writable=True,
    ),
) -> None:
    """Wizard interativo de configuração inicial. Grava o .env ao final."""
    env_path = Path(env_file) if env_file else _default_env()
    env_path.parent.mkdir(parents=True, exist_ok=True)

    store = EnvFile(env_path)
    existing = store.read()
    preserve = store.exists() and typer.confirm("Preservar valores já existentes no .env?", default=True)

    typer.echo(f"\nOrbita — Setup  ({env_path})\n")

    # ── Fase 1: ambiente ──────────────────────────────────────────
    _section("Fase 1: ambiente local")
    _ok(detect_python_status())
    typer.echo(f"  OK   install       modo {detect_install_mode()}")

    lm_inst = detect_lmstudio_installation()
    if lm_inst["ok"]:
        typer.echo(f"  OK   lmstudio-app  {lm_inst['path']}")
    else:
        typer.echo("  FAIL lmstudio-app  não encontrado")
        _open_url(LM_STUDIO_DOWNLOAD_URL, "LM Studio")

    # ── Fase 2: Telegram ─────────────────────────────────────────
    _section("Fase 2: Telegram Bot")
    typer.echo("  1. Abra o Telegram e procure @BotFather")
    typer.echo("  2. Envie /newbot e siga as instruções")
    typer.echo("  3. Cole o token abaixo\n")

    token = typer.prompt("  Token do bot", default=existing.get("TELEGRAM_BOT_TOKEN", ""), hide_input=False)
    try:
        identity = _run(validate_telegram_token_async(token))
        typer.echo(f"  OK   telegram      @{identity.get('username', '?')} validado")
    except Exception as exc:
        typer.echo(f"  FAIL telegram      {exc}")
        raise typer.Exit(code=1)

    typer.echo("\n  Envie qualquer mensagem para o seu bot agora.")
    typer.echo("  Vou detectar o seu user_id automaticamente (aguardo 60 s)...\n")
    discovered = _run(discover_telegram_user_async(token, timeout_seconds=60))
    if discovered:
        allowed_user_id = str(discovered["user_id"])
        typer.echo(f"  OK   user_id       {allowed_user_id} detectado automaticamente")
    else:
        typer.echo("  Não recebi mensagem a tempo.")
        allowed_user_id = typer.prompt(
            "  user_id do Telegram",
            default=existing.get("TELEGRAM_ALLOWED_USER_ID", ""),
        )

    # ── Fase 3: LM Studio + MCP ───────────────────────────────────
    _section("Fase 3: LM Studio e Windows-MCP")
    lmstudio_url = typer.prompt(
        "  URL do LM Studio",
        default=existing.get("LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_URL),
    )
    lm_result = probe_lmstudio(lmstudio_url, existing.get("LMSTUDIO_API_TOKEN", ""))
    _ok(lm_result)
    lmstudio_model = _choose_model(
        existing.get("LMSTUDIO_MODEL", "qwen3:4b"),
        lm_result.get("models", []),
    )

    enable_mcp = typer.confirm("\n  Ativar Windows-MCP no LM Studio?", default=True)
    mcp_mode = "disabled"
    mcp_plugin_id = existing.get("LMSTUDIO_MCP_PLUGIN_ID", DEFAULT_WINDOWS_MCP_PLUGIN_ID)
    mcp_server_url = existing.get("LMSTUDIO_MCP_SERVER_URL", "")
    mcp_label = existing.get("LMSTUDIO_MCP_SERVER_LABEL", DEFAULT_WINDOWS_MCP_LABEL)

    if enable_mcp:
        mcp_mode = typer.prompt(
            "  Modo MCP (plugin/ephemeral)",
            default=existing.get("LMSTUDIO_MCP_MODE", "plugin"),
        )
        if mcp_mode == "plugin":
            mcp_plugin_id = f"mcp/{mcp_label}"
            mcp_result = probe_windows_mcp(mode=mcp_mode, plugin_id=mcp_plugin_id)
            if not mcp_result["ok"]:
                _maybe_install_uv()
                if typer.confirm("  Escrever entrada Windows-MCP no mcp.json do LM Studio?", default=True):
                    config_path = write_windows_mcp_entry(label=mcp_label)
                    typer.echo(f"  OK   mcp-config    {config_path}")
        else:
            mcp_server_url = typer.prompt(
                "  URL do servidor MCP",
                default=mcp_server_url or "http://127.0.0.1:8000/mcp",
            )
        mcp_result = probe_windows_mcp(mode=mcp_mode, plugin_id=mcp_plugin_id, server_url=mcp_server_url)
        _ok(mcp_result)
        if not mcp_result["ok"]:
            _open_url(WINDOWS_MCP_URL, "Windows-MCP")

    # ── Fase 4: Ollama ────────────────────────────────────────────
    _section("Fase 4: Ollama")
    ollama_url = typer.prompt(
        "  URL do Ollama",
        default=existing.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    )
    ollama_result = probe_ollama(ollama_url)
    _ok(ollama_result)
    ollama_model = typer.prompt("  Modelo Ollama", default=existing.get("OLLAMA_MODEL", "qwen3:4b"))
    default_backend = typer.prompt(
        "  Backend padrão (lmstudio/ollama)",
        default=existing.get("BOT_DEFAULT_BACKEND", "ollama"),
    )

    # ── Grava .env ────────────────────────────────────────────────
    _section(f"Gravando configuração em {env_path}")
    data_dir = str(default_data_dir())
    values: dict[str, str] = {
        "TELEGRAM_BOT_TOKEN":         token,
        "TELEGRAM_ALLOWED_USER_ID":   allowed_user_id,
        "BOT_DEFAULT_BACKEND":        default_backend,
        "BOT_DATA_DIR":               existing.get("BOT_DATA_DIR", data_dir),
        "LMSTUDIO_BASE_URL":          lmstudio_url,
        "LMSTUDIO_API_TOKEN":         existing.get("LMSTUDIO_API_TOKEN", ""),
        "LMSTUDIO_MODEL":             lmstudio_model,
        "LMSTUDIO_MCP_MODE":          mcp_mode,
        "LMSTUDIO_MCP_PLUGIN_ID":     mcp_plugin_id,
        "LMSTUDIO_MCP_SERVER_URL":    mcp_server_url,
        "LMSTUDIO_MCP_SERVER_LABEL":  mcp_label,
        "LMSTUDIO_MCP_ALLOWED_TOOLS": existing.get(
            "LMSTUDIO_MCP_ALLOWED_TOOLS", ",".join(DEFAULT_WINDOWS_MCP_TOOLS)
        ),
        "OLLAMA_BASE_URL":            ollama_url,
        "OLLAMA_MODEL":               ollama_model,
    }
    merged = store.merge(values, preserve_existing=preserve)
    for k, v in values.items():
        if not preserve or k not in existing:
            merged[k] = v
    store.write(merged)
    typer.echo(f"  Salvo em: {env_path}")

    # ── Verificação final ─────────────────────────────────────────
    _section("Verificação final")
    results = _full_doctor(store.read())
    for r in results:
        _ok(r)

    passed = sum(1 for r in results if r.get("ok"))
    typer.echo(f"\n  {passed}/{len(results)} verificações OK")

    if passed >= 3:
        typer.echo("\n  Pronto! Para iniciar o Orbita:\n\n    orbita run\n")
    else:
        typer.echo("\n  Corrija os itens FAIL acima e rode orbita setup novamente.")
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# run
# ------------------------------------------------------------------

@app.command()
def run(
    env_file: Path = typer.Option(
        None,
        help="Caminho do .env. Padrão: %APPDATA%\\Orbita\\.env",
        exists=False, dir_okay=False,
    ),
) -> None:
    """Inicia o Orbita em modo polling."""
    run_bot(env_file=env_file or _default_env())


# ------------------------------------------------------------------
# doctor
# ------------------------------------------------------------------

@app.command()
def doctor(
    env_file: Path = typer.Option(
        None,
        help="Caminho do .env. Padrão: %APPDATA%\\Orbita\\.env",
        exists=False, dir_okay=False,
    ),
) -> None:
    """Verifica se todas as integrações estão funcionando."""
    values = EnvFile(env_file or _default_env()).read()
    typer.echo("\nOrbita — Diagnóstico\n")
    results = _full_doctor(values)
    for r in results:
        _ok(r)
    typer.echo("")
    if not all(r.get("ok") for r in results):
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# env
# ------------------------------------------------------------------

@app.command("env")
def env_command(
    env_file: Path = typer.Option(
        None,
        help="Caminho do .env. Padrão: %APPDATA%\\Orbita\\.env",
        exists=False, dir_okay=False,
    ),
    check: bool = typer.Option(False, "--check", help="Roda doctor após exibir os valores."),
) -> None:
    """Exibe as variáveis de ambiente configuradas."""
    path = env_file or _default_env()
    values = EnvFile(path).read()
    typer.echo(f"\nVariáveis em {path}:\n")
    for key in sorted(values):
        typer.echo(f"  {key}={_mask(key, values[key])}")
    if check:
        typer.echo("")
        for r in _full_doctor(values):
            _ok(r)


# ------------------------------------------------------------------
# skills
# ------------------------------------------------------------------

@app.command("skills")
def list_skills(
    skills_dir: Path = typer.Option(
        None,
        help="Pasta de skills. Padrão: %APPDATA%\\Orbita\\skills",
        exists=False, dir_okay=True,
    ),
) -> None:
    """Lista todas as skills carregadas."""
    folder = skills_dir or (default_data_dir() / "skills")
    registry = SkillRegistry(skills_dir=folder)
    registry.load()

    items = registry.skills
    if not items:
        typer.echo(f"Nenhuma skill encontrada em {folder.resolve()}")
        typer.echo("Crie pastas com SKILL.md dentro da pasta skills/ para adicionar capacidades.")
        return

    typer.echo(f"\nSkills em {folder.resolve()} ({len(items)} total)\n")
    labels = {"read": "Leitura", "write": "Modificação", "exec": "Execução"}
    groups: dict[str, list] = {"read": [], "write": [], "exec": []}
    for s in sorted(items, key=lambda x: x.name):
        groups.setdefault(s.risk_level, []).append(s)

    for risk in ("read", "write", "exec"):
        group = groups.get(risk, [])
        if not group:
            continue
        typer.echo(f"{RISK_ICON[risk]}  {labels[risk]}")
        for s in group:
            typer.echo(f"     {s.name:<22} {s.folder}")
        typer.echo("")

    typer.echo("Legenda: 🟢 seguro  🟡 cuidado  🔴 pede confirmação")


# ------------------------------------------------------------------
# check
# ------------------------------------------------------------------

@check_app.command("telegram")
def check_telegram(
    env_file: Path = typer.Option(None, exists=False, dir_okay=False),
) -> None:
    """Testa o token do Telegram."""
    token = EnvFile(env_file or _default_env()).read().get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        typer.echo("FAIL telegram — TELEGRAM_BOT_TOKEN não configurado")
        raise typer.Exit(code=1)
    try:
        identity = _run(validate_telegram_token_async(token))
        typer.echo(f"OK   telegram — @{identity.get('username', '?')}")
    except Exception as exc:
        typer.echo(f"FAIL telegram — {exc}")
        raise typer.Exit(code=1)


@check_app.command("lmstudio")
def check_lmstudio(
    env_file: Path = typer.Option(None, exists=False, dir_okay=False),
) -> None:
    """Testa a conexão com o LM Studio."""
    values = EnvFile(env_file or _default_env()).read()
    result = probe_lmstudio(
        values.get("LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_URL),
        values.get("LMSTUDIO_API_TOKEN", ""),
    )
    _ok(result)
    for m in result.get("models", [])[:5]:
        typer.echo(f"       modelo: {m}")
    if not result["ok"]:
        raise typer.Exit(code=1)


@check_app.command("mcp")
def check_mcp(
    env_file: Path = typer.Option(None, exists=False, dir_okay=False),
) -> None:
    """Testa a integração Windows-MCP."""
    values = EnvFile(env_file or _default_env()).read()
    result = probe_windows_mcp(
        mode=values.get("LMSTUDIO_MCP_MODE", "plugin"),
        plugin_id=values.get("LMSTUDIO_MCP_PLUGIN_ID", DEFAULT_WINDOWS_MCP_PLUGIN_ID),
        server_url=values.get("LMSTUDIO_MCP_SERVER_URL", ""),
    )
    _ok(result)
    if not result["ok"]:
        raise typer.Exit(code=1)


@check_app.command("ollama")
def check_ollama(
    env_file: Path = typer.Option(None, exists=False, dir_okay=False),
) -> None:
    """Testa a conexão com o Ollama."""
    values = EnvFile(env_file or _default_env()).read()
    result = probe_ollama(values.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    _ok(result)
    if not result["ok"]:
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------

def main() -> None:
    app()


if __name__ == "__main__":
    main()
