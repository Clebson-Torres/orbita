import pytest

from orbita.clients.lmstudio import LMStudioClient
from orbita.clients.lmstudio import LMStudioPayloadError, LMStudioToolError


def test_plugin_integrations_are_used_when_plugin_id_is_configured():
    client = LMStudioClient(
        base_url="http://127.0.0.1:1234",
        model="ibm/granite-4-micro",
        plugin_id="mcp/windows-mcp",
        allowed_tools=["Click-Tool", "Type-Tool"],
    )

    integrations = client._integrations()

    assert integrations == [
        {
            "type": "plugin",
            "id": "mcp/windows-mcp",
            "allowed_tools": ["Click-Tool", "Type-Tool"],
        }
    ]


def test_parse_payload_raises_tool_error_when_snapshot_is_missing():
    client = LMStudioClient(base_url="http://127.0.0.1:1234", model="ibm/granite-4-micro")

    payload = {
        "output": [
            {
                "type": "tool_call",
                "tool": "Click",
                "output": """[{"type":"text","text":"Error calling tool 'Click': Desktop state is empty. Please call Snapshot first."}]""",
            }
        ]
    }

    with pytest.raises(LMStudioToolError) as exc_info:
        client._parse_response(payload)

    assert "captura" in exc_info.value.safe_message.lower()


def test_parse_payload_raises_tool_error_for_malformed_type_call():
    client = LMStudioClient(base_url="http://127.0.0.1:1234", model="ibm/granite-4-micro")

    payload = {
        "output": [
            {
                "type": "tool_call",
                "tool": "Type",
                "output": """[{"type":"text","text":"Error calling tool 'Type': Either loc or label must be provided."}]""",
            }
        ]
    }

    with pytest.raises(LMStudioToolError) as exc_info:
        client._parse_response(payload)

    assert "Type" in str(exc_info.value)


def test_parse_payload_raises_payload_error_when_message_is_missing():
    client = LMStudioClient(base_url="http://127.0.0.1:1234", model="ibm/granite-4-micro")

    with pytest.raises(LMStudioPayloadError):
        client._parse_response({"output": [{"type": "reasoning", "content": "..."}, {"type": "tool_call", "tool": "Wait"}]})
