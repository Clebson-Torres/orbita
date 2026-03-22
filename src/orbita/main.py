from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from .app import TelegramPcBotApp
from .config import default_data_dir, default_env_file, load_settings


def _setup_logging(data_dir: Path) -> None:
    """Configura logging para arquivo quando rodando sem console (pythonw)."""
    log_file = data_dir / "orbita.log"
    handlers: list[logging.Handler] = [
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    # Só adiciona StreamHandler se houver console disponível (não pythonw)
    try:
        if sys.stdout and sys.stdout.fileno() >= 0:
            handlers.append(logging.StreamHandler(sys.stdout))
    except Exception:
        pass  # pythonw, service, ou redirect — sem console, tudo vai pro arquivo

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


async def _amain(env_file: Path) -> None:
    settings = load_settings(env_file)
    data_dir = settings.data_path
    data_dir.mkdir(parents=True, exist_ok=True)
    _setup_logging(data_dir)
    app = TelegramPcBotApp(settings, data_dir=data_dir)
    logging.getLogger(__name__).info("Orbita iniciado")
    try:
        await app.run()
    finally:
        await app.close()
        logging.getLogger(__name__).info("Orbita encerrado")


def run_bot(env_file: str | Path | None = None) -> None:
    path = Path(env_file) if env_file else default_env_file()
    try:
        asyncio.run(_amain(path))
    except ValidationError:
        msg = f"Configuração incompleta em {path}\nExecute: orbita setup"
        # Sem console, escreve no log de fallback
        fallback_log = default_data_dir() / "orbita.log"
        fallback_log.parent.mkdir(parents=True, exist_ok=True)
        with fallback_log.open("a", encoding="utf-8") as f:
            f.write(f"ERRO: {msg}\n")
        raise SystemExit(msg)
    except KeyboardInterrupt:
        pass


def main() -> None:
    run_bot()


if __name__ == "__main__":
    main()
