"""Núcleo do bot — loop de polling, roteamento e estado de sessão."""
from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .audit import AuditLog
from .clients.lmstudio import LMStudioError, LMStudioClient
from .clients.ollama import OllamaClient
from .clients.web_scraper import WebScraperClient
from .config import Settings
from .memory import PersistentMemory
from .native_actions import capture_screenshot, get_memory_summary
from .skills import SkillRegistry
from .telegram_api import TelegramAPI

BackendName = Literal["lmstudio", "ollama"]
logger = logging.getLogger(__name__)

DESTRUCTIVE_KEYWORDS = {
    "deleta", "apaga", "remove", "formata", "instala", "desinstala",
    "mata processo", "fecha tudo", "reinicia", "desliga",
}

NEWS_PORTALS = {
    "g1": "g1", "globo": "g1",
    "folha": "folha", "folha de sp": "folha",
    "bbc": "bbc_brasil", "bbc brasil": "bbc_brasil",
    "uol": "uol",
}
NEWS_SECTIONS = {
    "economia": "economia", "econom": "economia",
    "politica": "politica", "politic": "politica",
    "mundo": "mundo",
    "tecnologia": "tecnologia", "tech": "tecnologia",
    "poder": "poder",
    "mercado": "mercado",
}

# Ícone por nível de risco — visível no Telegram
RISK_ICON = {"read": "🟢", "write": "🟡", "exec": "🔴"}

BASE_SYSTEM_PROMPT = """Você é um assistente de desktop via Telegram, rodando no PC Windows do usuário.
Seja conciso. Para ações no PC, use as ferramentas MCP disponíveis.
Nunca execute ações destrutivas sem confirmação explícita do usuário.
Se uma ferramenta falhar duas vezes, pare e explique o erro.
Capture Snapshot antes de qualquer ação que dependa de labels na tela.
Nunca use Type sem loc ou label definido.
Screenshot e leitura de RAM são capacidades nativas do bot — prefira-as ao MCP.
Para notícias de portais conhecidos (G1, Folha, BBC, UOL), o bot busca RSS diretamente.
"""

HELP_TEXT = """\
Comandos disponíveis:

/start ou /help — esta mensagem
/status — backend ativo, dry-run, histórico
/model lmstudio|ollama — troca o backend
/dryrun on|off — simula ações sem executar
/reset — limpa memória da conversa
/skills — lista todas as skills carregadas
/news [portal] [seção] — notícias via RSS
/audit — últimas 20 ações registradas

Portais para /news: g1, folha, bbc, uol
Seções: principais, economia, politica, mundo, tecnologia

Legenda de risco das skills:
🟢 read — apenas leitura
🟡 write — modifica configurações
🔴 exec — executa processos (pede confirmação)\
"""


@dataclass(slots=True)
class SessionState:
    backend: BackendName
    history: list[dict[str, str]] = field(default_factory=list)
    awaiting_confirmation: str | None = None
    dry_run: bool = False


class TelegramPcBotApp:
    MAX_HISTORY = 12
    MAX_PROMPT_CHARS = 6000

    def __init__(self, settings: Settings, data_dir: Path | None = None) -> None:
        self._settings = settings
        self._telegram = TelegramAPI(settings.telegram_bot_token)
        self._lmstudio = LMStudioClient(
            base_url=settings.lmstudio_base_url,
            model=settings.lmstudio_model,
            api_token=settings.lmstudio_api_token,
            mcp_mode=settings.lmstudio_mcp_mode,
            plugin_id=settings.lmstudio_mcp_plugin_id,
            mcp_server_url=settings.lmstudio_mcp_server_url,
            mcp_server_label=settings.lmstudio_mcp_server_label,
            allowed_tools=settings.allowed_mcp_tools,
        )
        self._ollama = OllamaClient(base_url=settings.ollama_base_url, model=settings.ollama_model)
        self._scraper = WebScraperClient()

        base = data_dir or Path("data")
        self._memory = PersistentMemory(base / "memory.json")
        self._audit = AuditLog(base / "audit.log")
        self._skills = SkillRegistry(skills_dir=Path("skills"))
        self._skills.load()
        self._sessions: dict[int, SessionState] = {}

    async def close(self) -> None:
        await self._telegram.close()
        await self._lmstudio.close()
        await self._ollama.close()
        await self._scraper.close()

    async def run(self) -> None:
        offset: int | None = None
        while True:
            try:
                updates = await self._telegram.get_updates(offset=offset)
            except Exception:
                logger.exception("Polling falhou")
                continue
            for update in updates:
                update_id = update.get("update_id") if isinstance(update, dict) else getattr(update, "update_id", None)
                message = update.get("message") if isinstance(update, dict) else getattr(update, "message", None)
                if update_id is not None:
                    offset = int(update_id) + 1
                if not message:
                    continue
                try:
                    await self._handle_message(message)
                except Exception:
                    logger.exception("Falha ao processar update_id=%s", update_id)

    # ------------------------------------------------------------------
    # Handler principal
    # ------------------------------------------------------------------

    async def _handle_message(self, message: dict) -> None:
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = (message.get("text") or "").strip()

        if chat_id is None or user_id is None or not text:
            return
        if int(user_id) != self._settings.telegram_allowed_user_id:
            await self._telegram.send_message(int(chat_id), "Acesso negado.")
            return

        cid = int(chat_id)
        state = self._get_or_create_session(cid)

        if text.startswith("/"):
            await self._handle_command(cid, text, state)
            return

        if state.awaiting_confirmation:
            await self._handle_confirmation(cid, text, state)
            return

        native = _match_native_intent(text)
        if native == "screenshot":
            await self._handle_native_screenshot(cid, state)
            return
        if native == "memory":
            await self._handle_native_memory(cid, state)
            return
        if native == "news":
            await self._handle_native_news(cid, text, state)
            return

        if _is_destructive_intent(text) and not state.dry_run:
            state.awaiting_confirmation = text
            await self._telegram.send_message(
                cid,
                f"⚠️ Ação destrutiva detectada. Confirma?\n\n\"{text}\"\n\nResponda sim ou não.",
            )
            return

        await self._chat_with_llm(cid, text, state)

    # ------------------------------------------------------------------
    # Comandos /
    # ------------------------------------------------------------------

    async def _handle_command(self, chat_id: int, text: str, state: SessionState) -> None:
        cmd, *args = text.split(maxsplit=1)
        arg = args[0].strip() if args else ""

        match cmd.lower():
            case "/start" | "/help":
                await self._telegram.send_message(chat_id, HELP_TEXT)

            case "/status":
                dry = " | dry-run ON" if state.dry_run else ""
                conf = f"\nAguardando confirmação para: \"{state.awaiting_confirmation}\"" if state.awaiting_confirmation else ""
                skills_count = len(self._skills.skills)
                await self._telegram.send_message(
                    chat_id,
                    f"Backend: {state.backend}{dry}\n"
                    f"Histórico: {len(state.history)} mensagens\n"
                    f"Skills carregadas: {skills_count}{conf}",
                )

            case "/reset":
                state.history.clear()
                state.awaiting_confirmation = None
                self._memory.clear(chat_id)
                await self._telegram.send_message(chat_id, "Memória da conversa limpa.")

            case "/model" | "/backend":
                if arg.lower() not in {"lmstudio", "ollama"}:
                    await self._telegram.send_message(chat_id, "Use: /model lmstudio ou /model ollama")
                    return
                state.backend = arg.lower()  # type: ignore[assignment]
                await self._telegram.send_message(chat_id, f"Backend alterado para: {state.backend}")

            case "/dryrun":
                if arg.lower() == "on":
                    state.dry_run = True
                    await self._telegram.send_message(chat_id, "Dry-run ativado. Nenhuma ação será executada.")
                elif arg.lower() == "off":
                    state.dry_run = False
                    await self._telegram.send_message(chat_id, "Dry-run desativado. Ações reais.")
                else:
                    estado = "ON" if state.dry_run else "OFF"
                    await self._telegram.send_message(chat_id, f"Dry-run está {estado}. Use /dryrun on|off")

            case "/skills":
                await self._send_skills_list(chat_id)

            case "/audit":
                tail = self._audit.tail(20)
                await self._telegram.send_message(chat_id, f"```\n{tail}\n```")

            case "/news":
                parts = arg.lower().split()
                portal = NEWS_PORTALS.get(parts[0], "g1") if parts else "g1"
                section_key = parts[1] if len(parts) > 1 else "principais"
                section = NEWS_SECTIONS.get(section_key, section_key)
                await self._fetch_and_send_news(chat_id, portal, section, state)

            case _:
                await self._telegram.send_message(
                    chat_id,
                    f"Comando desconhecido: {cmd}\nUse /help para ver os comandos disponíveis.",
                )

    # ------------------------------------------------------------------
    # /skills — lista rica agrupada por nível de risco
    # ------------------------------------------------------------------

    async def _send_skills_list(self, chat_id: int) -> None:
        skills = self._skills.skills
        if not skills:
            await self._telegram.send_message(
                chat_id,
                "Nenhuma skill carregada.\n"
                "Crie pastas com SKILL.md dentro de skills/ e reinicie o bot.",
            )
            return

        # Agrupa por nível de risco
        groups: dict[str, list] = {"read": [], "write": [], "exec": []}
        for s in sorted(skills, key=lambda x: x.name):
            groups.setdefault(s.risk_level, []).append(s)

        lines = [f"Skills carregadas ({len(skills)} total)\n"]

        labels = {"read": "Leitura", "write": "Modificação", "exec": "Execução"}
        for risk in ("read", "write", "exec"):
            group = groups.get(risk, [])
            if not group:
                continue
            icon = RISK_ICON[risk]
            lines.append(f"{icon} {labels[risk]}")
            for s in group:
                lines.append(f"  • {s.name}")
            lines.append("")

        lines.append("🟢 seguro  🟡 cuidado  🔴 pede confirmação")

        await self._telegram.send_message(chat_id, "\n".join(lines))

    # ------------------------------------------------------------------
    # Confirmação de ações destrutivas
    # ------------------------------------------------------------------

    async def _handle_confirmation(self, chat_id: int, text: str, state: SessionState) -> None:
        normalized = _normalize(text)
        original = state.awaiting_confirmation
        state.awaiting_confirmation = None
        if normalized in {"sim", "s", "yes", "confirmar", "ok"}:
            self._audit.record(chat_id=chat_id, tool="confirmacao", status="confirmada", detail=original or "")
            await self._chat_with_llm(chat_id, original or text, state)
        else:
            self._audit.record(chat_id=chat_id, tool="confirmacao", status="cancelada", detail=original or "")
            await self._telegram.send_message(chat_id, "Ação cancelada.")

    # ------------------------------------------------------------------
    # Chat com LLM
    # ------------------------------------------------------------------

    async def _chat_with_llm(self, chat_id: int, text: str, state: SessionState) -> None:
        prompt = self._build_prompt(state.history, text)
        if state.dry_run:
            self._audit.record(chat_id=chat_id, tool="chat", status="dry-run", detail=text, dry_run=True)
            await self._telegram.send_message(
                chat_id,
                f"[dry-run] Prompt que seria enviado ao {state.backend}:\n```\n{prompt[-400:]}\n```",
            )
            return

        reply = await self._call_backend(chat_id, text, state)
        if reply is None:
            return

        state.history.append({"role": "user", "content": text})
        state.history.append({"role": "assistant", "content": reply})
        state.history = state.history[-self.MAX_HISTORY:]
        self._memory.save(chat_id, state.history)
        self._audit.record(chat_id=chat_id, tool="chat", status="ok", detail=reply[:80])
        await self._telegram.send_message(chat_id, reply)

    async def _call_backend(self, chat_id: int, text: str, state: SessionState) -> str | None:
        primary = state.backend
        fallback: BackendName = "ollama" if primary == "lmstudio" else "lmstudio"
        prompt = self._build_prompt(state.history, text)

        for backend in (primary, fallback):
            try:
                reply = await self._lmstudio.chat(prompt) if backend == "lmstudio" else await self._ollama.chat(prompt)
                if backend != primary:
                    await self._telegram.send_message(chat_id, f"_(fallback para {backend} — {primary} indisponível)_")
                return reply
            except LMStudioError as exc:
                if backend == fallback:
                    await self._telegram.send_message(chat_id, exc.safe_message)
                    return None
            except Exception:
                logger.exception("Backend %s falhou", backend)
                if backend == fallback:
                    await self._telegram.send_message(chat_id, "Ambos os backends falharam. Tente novamente.")
                    return None
        return None

    # ------------------------------------------------------------------
    # Notícias — RSS direto
    # ------------------------------------------------------------------

    async def _handle_native_news(self, chat_id: int, text: str, state: SessionState) -> None:
        lowered = _normalize(text)
        portal = "g1"
        section = "principais"
        for keyword, name in NEWS_PORTALS.items():
            if keyword in lowered:
                portal = name
                break
        for keyword, name in NEWS_SECTIONS.items():
            if keyword in lowered:
                section = name
                break
        await self._fetch_and_send_news(chat_id, portal, section, state)

    async def _fetch_and_send_news(self, chat_id: int, portal: str, section: str, state: SessionState) -> None:
        if state.dry_run:
            await self._telegram.send_message(chat_id, f"[dry-run] Buscaria RSS: {portal}/{section}")
            return
        try:
            items = await self._scraper.fetch_known(portal, section, max_items=8)
            self._audit.record(chat_id=chat_id, tool="RSS", status="ok", detail=f"{portal}/{section}")
        except Exception as exc:
            logger.exception("RSS falhou: %s/%s", portal, section)
            self._audit.record(chat_id=chat_id, tool="RSS", status="error", detail=str(exc))
            await self._telegram.send_message(chat_id, f"Não consegui buscar notícias de {portal}/{section}.")
            return

        if not items:
            await self._telegram.send_message(chat_id, "Nenhuma notícia encontrada.")
            return

        portal_label = portal.upper().replace("_BRASIL", " Brasil")
        section_label = section.capitalize()
        lines = [f"📰 {portal_label} — {section_label}\n"]
        for i, item in enumerate(items, 1):
            title = item.title or "(sem título)"
            lines.append(f"{i}. {title}")
            if item.link:
                lines.append(f"   {item.link}")

        raw = "\n".join(lines)
        if len(raw) > 500:
            try:
                summary_prompt = (
                    f"Aqui estão as manchetes do {portal_label} — {section_label}:\n\n{raw}\n\n"
                    "Apresente como lista numerada curta em português. Mantenha os links."
                )
                summary = await self._call_backend(chat_id, summary_prompt, state)
                if summary:
                    await self._telegram.send_message(chat_id, summary)
                    return
            except Exception:
                pass

        await self._telegram.send_message(chat_id, raw)

    # ------------------------------------------------------------------
    # Ações nativas
    # ------------------------------------------------------------------

    async def _handle_native_screenshot(self, chat_id: int, state: SessionState) -> None:
        path: Path | None = None
        try:
            if state.dry_run:
                await self._telegram.send_message(chat_id, "[dry-run] Capturaria screenshot.")
                return
            path = capture_screenshot()
            await self._telegram.send_photo(chat_id, path, caption="Screenshot agora")
            self._audit.record(chat_id=chat_id, tool="Screenshot", status="ok")
        except Exception:
            logger.exception("Screenshot falhou")
            self._audit.record(chat_id=chat_id, tool="Screenshot", status="error")
            await self._telegram.send_message(chat_id, "Não consegui capturar a tela.")
        finally:
            if path and path.exists():
                path.unlink(missing_ok=True)

    async def _handle_native_memory(self, chat_id: int, state: SessionState) -> None:
        try:
            if state.dry_run:
                await self._telegram.send_message(chat_id, "[dry-run] Leria uso de RAM.")
                return
            summary = get_memory_summary()
            self._audit.record(chat_id=chat_id, tool="MemorySummary", status="ok")
            await self._telegram.send_message(chat_id, summary)
        except Exception:
            logger.exception("RAM summary falhou")
            self._audit.record(chat_id=chat_id, tool="MemorySummary", status="error")
            await self._telegram.send_message(chat_id, "Não consegui ler a memória.")

    # ------------------------------------------------------------------
    # Sessão e prompt
    # ------------------------------------------------------------------

    def _get_or_create_session(self, chat_id: int) -> SessionState:
        if chat_id not in self._sessions:
            self._sessions[chat_id] = SessionState(
                backend=self._settings.bot_default_backend,
                history=self._memory.load(chat_id),
            )
        return self._sessions[chat_id]

    def _build_prompt(self, history: list[dict[str, str]], user_text: str) -> str:
        skills_block = self._skills.as_system_block()
        system = BASE_SYSTEM_PROMPT + ("\n\n" + skills_block if skills_block else "")
        lines = [system, "", "Conversa:"]
        for entry in history[-self.MAX_HISTORY:]:
            lines.append(f"{entry['role']}: {entry['content'][:800]}")
        lines.append(f"user: {user_text}")
        prompt = "\n".join(lines)
        return prompt[-self.MAX_PROMPT_CHARS:] if len(prompt) > self.MAX_PROMPT_CHARS else prompt


# ------------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------------

def _normalize(text: str) -> str:
    nkfd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nkfd if not unicodedata.combining(c)).lower().strip()


def _match_native_intent(text: str) -> str | None:
    lowered = _normalize(text)
    if any(p in lowered for p in ["tirar print", "screenshot", "captura a tela", "manda print"]):
        return "screenshot"
    if any(p in lowered for p in ["memoria", "uso de ram", "ram agora", "memoria usada"]):
        return "memory"
    if any(p in lowered for p in ["noticia", "manchete", "g1", "folha", "bbc", "uol", "hoje no jornal"]):
        return "news"
    return None


def _is_destructive_intent(text: str) -> bool:
    lowered = _normalize(text)
    return any(k in lowered for k in DESTRUCTIVE_KEYWORDS)
