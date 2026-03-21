"""Memória persistente de conversas entre sessões.

Salva o histórico de cada chat_id em disco (JSON).
Na próxima vez que o bot reiniciar, a conversa continua
de onde parou.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cada entrada: {"role": "user"|"assistant", "content": "..."}
HistoryEntry = dict[str, str]


class PersistentMemory:
    """Armazena e recupera histórico de conversas em arquivo JSON.

    Uso:
        memory = PersistentMemory(Path("data/memory.json"))
        history = memory.load(chat_id)
        memory.save(chat_id, history)
        memory.clear(chat_id)
    """

    def __init__(self, path: Path, max_entries_per_chat: int = 40) -> None:
        self._path = path
        self._max = max_entries_per_chat
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, list[HistoryEntry]] = self._read()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def load(self, chat_id: int) -> list[HistoryEntry]:
        """Retorna histórico do chat. Lista vazia se ainda não existe."""
        return list(self._data.get(str(chat_id), []))

    def save(self, chat_id: int, history: list[HistoryEntry]) -> None:
        """Persiste o histórico do chat em disco (trunca se necessário)."""
        trimmed = history[-self._max :]
        self._data[str(chat_id)] = trimmed
        self._write()

    def clear(self, chat_id: int) -> None:
        """Apaga todo o histórico de um chat."""
        self._data.pop(str(chat_id), None)
        self._write()

    def all_chat_ids(self) -> list[int]:
        """Lista todos os chats que têm histórico salvo."""
        return [int(k) for k in self._data]

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _read(self) -> dict[str, list[HistoryEntry]]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Falha ao ler memory.json — iniciando vazio.", exc_info=True)
            return {}

    def _write(self) -> None:
        try:
            self._path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            logger.error("Falha ao salvar memory.json.", exc_info=True)
