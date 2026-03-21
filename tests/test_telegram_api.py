import httpx
import pytest

from orbita.telegram_api import TelegramAPI


def build_client(handler):
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


@pytest.mark.anyio
async def test_validate_token_returns_bot_identity():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/getMe")
        return httpx.Response(
            200,
            json={"ok": True, "result": {"id": 42, "username": "desktop_bot", "is_bot": True}},
        )

    api = TelegramAPI("token", client=build_client(handler))
    result = await api.get_me()

    assert result["id"] == 42
    assert result["username"] == "desktop_bot"
    await api.close()


@pytest.mark.anyio
async def test_wait_for_new_message_returns_latest_user_and_chat():
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"ok": True, "result": [{"update_id": 10}]})
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 11,
                        "message": {
                            "chat": {"id": 555},
                            "from": {"id": 999, "username": "clebs"},
                            "text": "hello",
                        },
                    }
                ],
            },
        )

    api = TelegramAPI("token", client=build_client(handler))
    result = await api.wait_for_new_message(timeout_seconds=2, poll_interval_seconds=0)

    assert result is not None
    assert result["user_id"] == 999
    assert result["chat_id"] == 555
    await api.close()


@pytest.mark.anyio
async def test_send_photo_uploads_file_to_telegram(tmp_path):
    image_path = tmp_path / "screen.png"
    image_path.write_bytes(b"fake-image-bytes")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/sendPhoto")
        body = await request.aread()
        assert b'name="chat_id"' in body
        assert b'name="caption"' in body
        assert b'name="photo"; filename="screen.png"' in body
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    api = TelegramAPI("token", client=build_client(handler))
    await api.send_photo(555, image_path, caption="Screenshot capturado agora")
    await api.close()
