"""Sistema de Skills — carrega habilidades do bot a partir de pastas.

Cada skill é uma pasta dentro de `skills/` com um arquivo `SKILL.md`
descrevendo quando e como o bot deve usá-la. O conteúdo de todos os
SKILL.md é injetado no system prompt antes de cada chamada ao LLM,
dando ao modelo consciência das capacidades disponíveis.

Estrutura esperada:
    skills/
        screenshot/
            SKILL.md
        clipboard/
            SKILL.md
        process_manager/
            SKILL.md
            list_procs.ps1
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

SKILL_FILENAME = "SKILL.md"


@dataclass
class Skill:
    name: str
    description: str          # conteúdo do SKILL.md
    folder: Path
    risk_level: str = "read"  # "read" | "write" | "exec"

    def __str__(self) -> str:
        return f"[skill:{self.name}]\n{self.description}"


@dataclass
class SkillRegistry:
    """Carrega e mantém todas as skills disponíveis."""

    skills_dir: Path
    _skills: list[Skill] = field(default_factory=list)

    def load(self) -> None:
        """Varre a pasta de skills e carrega os SKILL.md encontrados."""
        self._skills = []
        if not self.skills_dir.exists():
            logger.info("Pasta de skills não encontrada: %s", self.skills_dir)
            return

        for folder in sorted(self.skills_dir.iterdir()):
            if not folder.is_dir():
                continue
            skill_file = folder / SKILL_FILENAME
            if not skill_file.exists():
                continue
            try:
                content = skill_file.read_text(encoding="utf-8").strip()
                risk = self._detect_risk(content)
                self._skills.append(
                    Skill(name=folder.name, description=content, folder=folder, risk_level=risk)
                )
                logger.debug("Skill carregada: %s (risco=%s)", folder.name, risk)
            except Exception:
                logger.warning("Falha ao carregar skill: %s", folder.name, exc_info=True)

        logger.info("%d skill(s) carregada(s).", len(self._skills))

    @property
    def skills(self) -> list[Skill]:
        return list(self._skills)

    def as_system_block(self) -> str:
        """Retorna bloco de texto para injetar no system prompt."""
        if not self._skills:
            return ""
        lines = ["## Skills disponíveis", ""]
        for skill in self._skills:
            lines.append(str(skill))
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Heurística de risco — lê palavras-chave do SKILL.md
    # ------------------------------------------------------------------

    _EXEC_KEYWORDS = {"powershell", "executa", "process", "launch", "run", "shell"}
    _WRITE_KEYWORDS = {"write", "escreve", "clipboard", "type", "deleta", "cria arquivo"}

    def _detect_risk(self, content: str) -> str:
        lower = content.lower()
        if any(k in lower for k in self._EXEC_KEYWORDS):
            return "exec"
        if any(k in lower for k in self._WRITE_KEYWORDS):
            return "write"
        return "read"
