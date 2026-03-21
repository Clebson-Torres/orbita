from pathlib import Path

from orbita.env_file import ENV_ORDER, EnvFile


def test_read_write_and_preserve_existing_values(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "TELEGRAM_BOT_TOKEN=old-token\n"
        "TELEGRAM_ALLOWED_USER_ID=123\n"
        "BOT_DEFAULT_BACKEND=lmstudio\n",
        encoding="utf-8",
    )

    store = EnvFile(env_path)
    merged = store.merge(
        {
            "TELEGRAM_BOT_TOKEN": "new-token",
            "LMSTUDIO_MODEL": "ibm/granite-4-micro",
        },
        preserve_existing=True,
    )

    assert merged["TELEGRAM_BOT_TOKEN"] == "old-token"
    assert merged["LMSTUDIO_MODEL"] == "ibm/granite-4-micro"

    store.write(merged)
    saved = env_path.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=old-token" in saved
    assert "LMSTUDIO_MODEL=ibm/granite-4-micro" in saved
    assert saved.splitlines()[0].startswith(ENV_ORDER[0])


def test_merge_can_overwrite_existing_values(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("TELEGRAM_BOT_TOKEN=old-token\n", encoding="utf-8")

    store = EnvFile(env_path)
    merged = store.merge({"TELEGRAM_BOT_TOKEN": "new-token"}, preserve_existing=False)

    assert merged["TELEGRAM_BOT_TOKEN"] == "new-token"

