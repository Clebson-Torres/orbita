"""Testes do roteador e lógica central do app.

Adaptados para a API atual do TelegramPcBotApp:
  - _build_prompt(self, history, text) — instância, history como list[dict]
  - _match_native_intent(text) — função de módulo
  - _is_destructive_intent(text) — função de módulo
  - screenshot/memory chamam funções importadas (mockadas via monkeypatch)
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import anyio
import pytest

from orbita.app import (
    TelegramPcBotApp,
    _match_native_intent,
    _is_destructive_intent,
)
from orbita.clients.lmstudio import LMStudioError
from orbita.config import Settings


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def make_settings(**kwargs) -> Settings:
    defaults = dict(
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_ALLOWED_USER_ID=123,
    )
    defaults.update(kwargs)
    return Settings(**defaults)


def make_app(tmp_path: Path) -> TelegramPcBotApp:
    return TelegramPcBotApp(make_settings(), data_dir=tmp_path / "data")


# ------------------------------------------------------------------
# _build_prompt
# ------------------------------------------------------------------

def test_build_prompt_contains_user_message(tmp_path):
    app = make_app(tmp_path)
    history = [{"role": "user", "content": "hello"}]
    prompt = app._build_prompt(history, "open notepad")
    assert "open notepad" in prompt
    assert "hello" in prompt
    assert "Snapshot" in prompt


def test_build_prompt_trims_long_history(tmp_path):
    app = make_app(tmp_path)
    history = [{"role": "user", "content": f"message {i} " + "x" * 900} for i in range(10)]
    prompt = app._build_prompt(history, "open browser now")
    assert "open browser now" in prompt
    assert "message 0" not in prompt
    assert len(prompt) <= app.MAX_PROMPT_CHARS + 200  # margem para system prompt


# ------------------------------------------------------------------
# _match_native_intent (função de módulo)
# ------------------------------------------------------------------

def test_match_native_intent_screenshot():
    assert _match_native_intent("tirar print da tela") == "screenshot"
    assert _match_native_intent("manda um screenshot") == "screenshot"
    assert _match_native_intent("captura a tela agora") == "screenshot"


def test_match_native_intent_memory():
    assert _match_native_intent("verificar memoria") == "memory"
    assert _match_native_intent("qual o uso de ram agora") == "memory"
    assert _match_native_intent("verificar memória") == "memory"


def test_match_native_intent_news():
    assert _match_native_intent("quais as noticias de hoje") == "news"
    assert _match_native_intent("manchetes do g1") == "news"
    assert _match_native_intent("noticias do uol") == "news"


def test_match_native_intent_none():
    assert _match_native_intent("abre o notepad") is None
    assert _match_native_intent("qual a temperatura da cpu") is None


# ------------------------------------------------------------------
# _is_destructive_intent (função de módulo)
# ------------------------------------------------------------------

def test_is_destructive_intent():
    assert _is_destructive_intent("deleta os arquivos temporários") is True
    assert _is_destructive_intent("desliga o computador") is True
    assert _is_destructive_intent("abre o chrome") is False
    assert _is_destructive_intent("qual meu ip") is False


# ------------------------------------------------------------------
# _handle_message — screenshot nativo
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_handle_message_uses_native_screenshot(tmp_path):
    app = make_app(tmp_path)

    screenshot_path = tmp_path / "screen.png"
    screenshot_path.write_bytes(b"fake-image-bytes")
    sent_photos: list[tuple[int, str]] = []

    class FakeTelegram:
        async def send_message(self, chat_id, text):
            raise AssertionError(f"send_message inesperado: {text}")
        async def send_photo(self, chat_id, photo_path, caption=""):
            sent_photos.append((chat_id, caption))
        async def close(self): pass
        async def get_updates(self, **kw): return []

    app._telegram = FakeTelegram()

    with patch("orbita.app.capture_screenshot", return_value=screenshot_path):
        await app._handle_message({
            "chat": {"id": 1},
            "from": {"id": 123},
            "text": "tirar print da tela",
        })

    assert sent_photos == [(1, "Screenshot agora")]


@pytest.mark.anyio
async def test_handle_message_screenshot_failure(tmp_path):
    app = make_app(tmp_path)
    sent: list[str] = []

    class FakeTelegram:
        async def send_message(self, chat_id, text): sent.append(text)
        async def send_photo(self, *a, **kw): pass
        async def close(self): pass

    app._telegram = FakeTelegram()

    with patch("orbita.app.capture_screenshot", side_effect=RuntimeError("falhou")):
        await app._handle_message({
            "chat": {"id": 1},
            "from": {"id": 123},
            "text": "captura a tela",
        })

    assert any("capturar" in m or "consegui" in m for m in sent)


# ------------------------------------------------------------------
# _handle_message — memória nativa
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_handle_message_memory_summary(tmp_path):
    app = make_app(tmp_path)
    sent: list[str] = []

    class FakeTelegram:
        async def send_message(self, chat_id, text): sent.append(text)
        async def close(self): pass

    app._telegram = FakeTelegram()

    with patch("orbita.app.get_memory_summary", return_value="RAM: 8 GB / 16 GB (50%)"):
        await app._handle_message({
            "chat": {"id": 1},
            "from": {"id": 123},
            "text": "verificar memoria",
        })

    assert sent == ["RAM: 8 GB / 16 GB (50%)"]


# ------------------------------------------------------------------
# _handle_message — LMStudioError vira mensagem segura
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_handle_message_lmstudio_error_returns_safe_message(tmp_path):
    app = make_app(tmp_path)
    sent: list[str] = []

    class FakeTelegram:
        async def send_message(self, chat_id, text): sent.append(text)
        async def close(self): pass

    class FailLMStudio:
        async def chat(self, prompt):
            raise LMStudioError("state empty", safe_message="LM Studio indisponível.")
        async def close(self): pass

    class FailOllama:
        async def chat(self, prompt):
            raise RuntimeError("ollama offline")
        async def close(self): pass

    app._telegram = FakeTelegram()
    app._lmstudio = FailLMStudio()
    app._ollama = FailOllama()

    await app._handle_message({
        "chat": {"id": 1},
        "from": {"id": 123},
        "text": "abre o navegador",
    })

    assert len(sent) >= 1
    assert any("indispon" in m or "falh" in m or "backend" in m.lower() for m in sent)


# ------------------------------------------------------------------
# _handle_message — acesso negado
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_handle_message_denies_unauthorized_user(tmp_path):
    app = make_app(tmp_path)
    sent: list[str] = []

    class FakeTelegram:
        async def send_message(self, chat_id, text): sent.append(text)
        async def close(self): pass

    app._telegram = FakeTelegram()

    await app._handle_message({
        "chat": {"id": 1},
        "from": {"id": 999},   # user_id diferente do autorizado (123)
        "text": "oi",
    })

    assert sent == ["Acesso negado."]


# ------------------------------------------------------------------
# _handle_message — confirmação de ação destrutiva
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_handle_message_asks_confirmation_for_destructive(tmp_path):
    app = make_app(tmp_path)
    sent: list[str] = []

    class FakeTelegram:
        async def send_message(self, chat_id, text): sent.append(text)
        async def close(self): pass

    app._telegram = FakeTelegram()

    await app._handle_message({
        "chat": {"id": 1},
        "from": {"id": 123},
        "text": "deleta os arquivos temporários",
    })

    assert len(sent) == 1
    assert "⚠️" in sent[0] or "destrutiva" in sent[0].lower()


# ------------------------------------------------------------------
# run() — continua após falha em uma mensagem
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_run_continues_after_message_failure(tmp_path):
    app = make_app(tmp_path)
    processed: list[str] = []

    class FakeTelegram:
        def __init__(self):
            self.calls = 0
        async def get_updates(self, offset=None, timeout=30):
            self.calls += 1
            if self.calls == 1:
                return [
                    {"update_id": 1, "message": {"text": "first"}},
                    {"update_id": 2, "message": {"text": "second"}},
                ]
            await anyio.sleep(60)
            return []
        async def close(self): pass

    async def fake_handle(message):
        processed.append(message["text"])
        if message["text"] == "first":
            raise RuntimeError("boom")

    app._telegram = FakeTelegram()
    app._handle_message = fake_handle

    async with anyio.create_task_group() as tg:
        tg.start_soon(app.run)
        await anyio.sleep(0.05)
        tg.cancel_scope.cancel()

    assert processed == ["first", "second"]
