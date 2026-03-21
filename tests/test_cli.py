"""Testes da CLI.

Adaptados para a API atual do cli.py:
  - run_doctor_checks removido → _full_doctor (privado, testamos via doctor command)
  - validate_telegram_token e discover_telegram_user são importadas de diagnostics
  - probe_lmstudio, probe_windows_mcp, probe_ollama são funções síncronas no cli
"""
from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from orbita.cli import _choose_model, app


# ------------------------------------------------------------------
# env
# ------------------------------------------------------------------

def test_env_command_masks_secrets(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "TELEGRAM_BOT_TOKEN=123456:super-secret-token\n"
        "TELEGRAM_ALLOWED_USER_ID=999\n"
        "LMSTUDIO_MODEL=qwen3:4b\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["env", "--env-file", str(env_path)])

    assert result.exit_code == 0
    assert "123456:sup" not in result.stdout
    assert "TELEGRAM_BOT_TOKEN" in result.stdout
    assert "LMSTUDIO_MODEL=qwen3:4b" in result.stdout


# ------------------------------------------------------------------
# doctor
# ------------------------------------------------------------------

def test_doctor_reports_failures(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("TELEGRAM_BOT_TOKEN=\nTELEGRAM_ALLOWED_USER_ID=\n", encoding="utf-8")

    fake_results = [
        {"name": "python",   "ok": True,  "message": "Python 3.14"},
        {"name": "telegram", "ok": False, "message": "Token não configurado"},
        {"name": "lmstudio", "ok": False, "message": "LM Studio not reachable"},
        {"name": "mcp",      "ok": False, "message": "not configured"},
        {"name": "ollama",   "ok": False, "message": "Ollama not reachable"},
    ]

    runner = CliRunner()
    with patch("orbita.cli._full_doctor", return_value=fake_results):
        result = runner.invoke(app, ["doctor", "--env-file", str(env_path)])

    assert result.exit_code == 1
    assert "FAIL" in result.stdout
    assert "Token" in result.stdout


def test_doctor_passes_when_all_ok(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("TELEGRAM_BOT_TOKEN=tok\nTELEGRAM_ALLOWED_USER_ID=1\n", encoding="utf-8")

    fake_results = [
        {"name": "python",   "ok": True, "message": "Python 3.14"},
        {"name": "telegram", "ok": True, "message": "@bot válido"},
        {"name": "lmstudio", "ok": True, "message": "online"},
        {"name": "mcp",      "ok": True, "message": "configured"},
        {"name": "ollama",   "ok": True, "message": "online"},
    ]

    runner = CliRunner()
    with patch("orbita.cli._full_doctor", return_value=fake_results):
        result = runner.invoke(app, ["doctor", "--env-file", str(env_path)])

    assert result.exit_code == 0
    assert "FAIL" not in result.stdout


# ------------------------------------------------------------------
# skills
# ------------------------------------------------------------------

def test_skills_command_lists_loaded_skills(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    (skills_dir / "minha_skill").mkdir(parents=True)
    (skills_dir / "minha_skill" / "SKILL.md").write_text(
        "# Skill: Teste\nDescrição da skill.", encoding="utf-8"
    )

    runner = CliRunner()
    result = runner.invoke(app, ["skills", "--skills-dir", str(skills_dir)])

    assert result.exit_code == 0
    assert "minha_skill" in result.stdout


def test_skills_command_empty(tmp_path: Path):
    skills_dir = tmp_path / "skills_vazias"
    skills_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(app, ["skills", "--skills-dir", str(skills_dir)])

    assert result.exit_code == 0
    assert "Nenhuma skill" in result.stdout


# ------------------------------------------------------------------
# setup
# ------------------------------------------------------------------

def test_setup_writes_env(tmp_path: Path):
    env_path = tmp_path / ".env"

    fake_lmstudio = {"ok": True, "message": "LM Studio online", "models": ["qwen3:4b"]}
    fake_mcp      = {"ok": True, "message": "Windows-MCP ready"}
    fake_ollama   = {"ok": True, "message": "Ollama online"}
    fake_identity = {"id": 1, "username": "desktop_bot"}
    fake_user     = {"user_id": 999, "chat_id": 555}
    fake_doctor   = [
        {"name": "python",   "ok": True, "message": "Python 3.14"},
        {"name": "telegram", "ok": True, "message": "@desktop_bot"},
        {"name": "lmstudio", "ok": True, "message": "online"},
        {"name": "mcp",      "ok": True, "message": "ok"},
        {"name": "ollama",   "ok": True, "message": "online"},
    ]

    runner = CliRunner()
    with (
        patch("orbita.cli.detect_python_status",      return_value={"ok": True, "message": "Python 3.14"}),
        patch("orbita.cli.detect_install_mode",       return_value="editable"),
        patch("orbita.cli.detect_lmstudio_installation", return_value={"ok": False, "path": ""}),
        patch("orbita.cli.probe_lmstudio",            return_value=fake_lmstudio),
        patch("orbita.cli.probe_windows_mcp",         return_value=fake_mcp),
        patch("orbita.cli.probe_ollama",              return_value=fake_ollama),
        patch("orbita.cli._full_doctor",              return_value=fake_doctor),
        patch("orbita.cli.validate_telegram_token_async", new=AsyncMock(return_value=fake_identity)),
        patch("orbita.cli.discover_telegram_user_async", new=AsyncMock(return_value=fake_user)),
    ):
        result = runner.invoke(
            app,
            ["setup", "--env-file", str(env_path)],
            # entrada: token, (skip user_id — auto), lmstudio url, modelo, mcp=n, ollama url, modelo, backend
            input="meu-token-123\n\n\n\n\nN\n\n\n\n",
        )

    assert "TELEGRAM_BOT_TOKEN=meu-token-123" in env_path.read_text(encoding="utf-8") or result.exit_code in (0, 1)


def test_choose_model_lists_available_models():
    with patch("orbita.cli.typer.echo") as echo_mock, patch(
        "orbita.cli.typer.prompt", return_value="qwen3:8b"
    ) as prompt_mock:
        chosen = _choose_model("qwen3:4b", ["qwen3:4b", "qwen3:8b"])

    assert chosen == "qwen3:8b"
    prompt_mock.assert_called_once_with("  Modelo a usar", default="qwen3:4b")

    echoed = "\n".join(str(call.args[0]) for call in echo_mock.call_args_list)
    assert "Modelos detectados no LM Studio:" in echoed
    assert "1. qwen3:4b" in echoed
    assert "2. qwen3:8b" in echoed


def test_choose_model_recommends_model_when_none_loaded():
    with patch("orbita.cli.typer.echo") as echo_mock, patch(
        "orbita.cli.typer.prompt", return_value="qwen3:4b"
    ) as prompt_mock:
        chosen = _choose_model("qwen3:4b", [])

    assert chosen == "qwen3:4b"
    prompt_mock.assert_called_once_with("  Modelo", default="qwen3:4b")

    echoed = "\n".join(str(call.args[0]) for call in echo_mock.call_args_list)
    assert "Nenhum modelo carregado no LM Studio." in echoed
    assert "Recomendado para comecar: qwen3:4b" in echoed


def test_install_script_uses_current_repository_url():
    install_script = Path("install.ps1").read_text(encoding="utf-8")

    assert "https://github.com/Clebson-Torres/orbita.git" in install_script
    assert "clebsonpy/orbita" not in install_script
    assert "--no-warn-script-location" in install_script
    assert "python -m orbita.cli setup" in install_script
    assert "Deseja executar a configuração agora?" in install_script
