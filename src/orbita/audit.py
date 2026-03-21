"""Audit log — registra toda ação executada pelo bot.

Cada linha do arquivo de log segue o formato:
    [2026-03-21 14:32:01] CHAT=123 TOOL=Snapshot STATUS=ok DETAIL=...

Isso permite auditar o que o bot fez, quando e com qual resultado,
sem depender do log geral da aplicação.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLog:
    """Registra ações do bot em arquivo de texto simples."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        chat_id: int,
        tool: str,
        status: str,
        detail: str = "",
        dry_run: bool = False,
    ) -> None:
        """Registra uma ação no log de auditoria."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mode = "DRY-RUN" if dry_run else "EXEC"
        line = f"[{now}] CHAT={chat_id} MODE={mode} TOOL={tool} STATUS={status}"
        if detail:
            # Trunca para não inflar o arquivo com respostas longas
            line += f" DETAIL={detail[:120].replace(chr(10), ' ')}"
        line += "\n"
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except Exception:
            logger.error("Falha ao escrever audit log.", exc_info=True)

    def tail(self, n: int = 20) -> str:
        """Retorna as últimas n linhas do log (para /audit no Telegram)."""
        if not self._path.exists():
            return "Log vazio."
        lines = self._path.read_text(encoding="utf-8").splitlines()
        return "\n".join(lines[-n:]) or "Log vazio."
