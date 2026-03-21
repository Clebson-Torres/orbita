from orbita.config import Settings


def test_allowed_mcp_tools_are_parsed():
    settings = Settings(
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_ALLOWED_USER_ID=123,
        LMSTUDIO_MCP_ALLOWED_TOOLS="Click, Type,Wait",
    )
    assert settings.allowed_mcp_tools == ["Click", "Type", "Wait"]

