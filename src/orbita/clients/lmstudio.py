from __future__ import annotations

import json
from typing import Any

import httpx


class LMStudioError(RuntimeError):
    def __init__(self, message: str, safe_message: str | None = None) -> None:
        super().__init__(message)
        self.safe_message = safe_message or "LM Studio falhou nesta acao. Tente novamente em instantes."


class LMStudioHTTPError(LMStudioError):
    pass


class LMStudioPayloadError(LMStudioError):
    pass


class LMStudioToolError(LMStudioError):
    pass


class LMStudioClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_token: str = "",
        mcp_mode: str = "plugin",
        plugin_id: str = "",
        mcp_server_url: str = "",
        mcp_server_label: str = "windows-mcp",
        allowed_tools: list[str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_token = api_token
        self._mcp_mode = mcp_mode
        self._plugin_id = plugin_id
        self._mcp_server_url = mcp_server_url
        self._mcp_server_label = mcp_server_label
        self._allowed_tools = allowed_tools or []
        self._client = client or httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_token:
            headers["Authorization"] = f"Bearer {self._api_token}"
        return headers

    def _integrations(self) -> list[dict[str, Any]]:
        if self._mcp_mode == "plugin" and self._plugin_id:
            return [
                {
                    "type": "plugin",
                    "id": self._plugin_id,
                    "allowed_tools": self._allowed_tools,
                }
            ]
        if self._mcp_mode != "ephemeral" or not self._mcp_server_url:
            return []
        return [
            {
                "type": "ephemeral_mcp",
                "server_label": self._mcp_server_label,
                "server_url": self._mcp_server_url,
                "allowed_tools": self._allowed_tools,
            }
        ]

    async def chat(self, prompt: str) -> str:
        body: dict[str, Any] = {
            "model": self._model,
            "input": prompt,
        }
        integrations = self._integrations()
        if integrations:
            body["integrations"] = integrations

        try:
            response = await self._client.post(f"{self._base_url}/api/v1/chat", headers=self._headers(), json=body)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 403:
                raise LMStudioHTTPError(
                    f"LM Studio returned HTTP 403 for {exc.request.url}",
                    safe_message="LM Studio recusou a chamada. Verifique o token da API e as permissoes MCP no LM Studio.",
                ) from exc
            raise LMStudioHTTPError(
                f"LM Studio returned HTTP {status_code} for {exc.request.url}",
                safe_message="LM Studio falhou nesta acao. Tente novamente em instantes.",
            ) from exc
        except httpx.HTTPError as exc:
            raise LMStudioHTTPError(
                f"LM Studio request failed: {exc}",
                safe_message="Nao consegui falar com o LM Studio. Confira se ele esta rodando na porta esperada.",
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise LMStudioPayloadError(
                "LM Studio returned invalid JSON",
                safe_message="LM Studio respondeu em formato invalido. Tente novamente.",
            ) from exc
        return self._parse_response(payload)

    async def list_models(self) -> list[str]:
        response = await self._client.get(f"{self._base_url}/api/v1/models", headers=self._headers())
        response.raise_for_status()
        payload = response.json()
        raw_models = payload.get("data") or payload.get("models") or []
        models: list[str] = []
        for item in raw_models:
            if isinstance(item, dict):
                model_id = item.get("id") or item.get("model_key") or item.get("identifier")
                if model_id:
                    models.append(str(model_id))
            elif isinstance(item, str):
                models.append(item)
        return models

    def _parse_response(self, payload: dict[str, Any]) -> str:
        output = payload.get("output", [])
        tool_errors = self._extract_tool_errors(output)
        if tool_errors:
            raise LMStudioToolError("; ".join(tool_errors), safe_message=self._build_tool_error_message(tool_errors))

        parts: list[str] = []
        for item in output:
            if item.get("type") == "message" and item.get("content"):
                parts.append(str(item["content"]))
        if not parts:
            raise LMStudioPayloadError(
                f"LM Studio response did not contain a message: {payload}",
                safe_message="LM Studio nao devolveu uma resposta util. Tente pedir a acao de forma mais curta.",
            )
        return "\n".join(parts).strip()

    @staticmethod
    def _extract_tool_errors(output: list[dict[str, Any]]) -> list[str]:
        errors: list[str] = []
        for item in output:
            if item.get("type") != "tool_call":
                continue
            tool_output = item.get("output")
            if not tool_output:
                continue
            if isinstance(tool_output, str):
                if "Error calling tool" in tool_output:
                    errors.append(tool_output)
                    continue
                try:
                    parsed_output = json.loads(tool_output)
                except json.JSONDecodeError:
                    parsed_output = []
            else:
                parsed_output = tool_output
            if isinstance(parsed_output, list):
                for part in parsed_output:
                    text = str(part.get("text", "")) if isinstance(part, dict) else str(part)
                    if "Error calling tool" in text:
                        errors.append(text)
        return errors

    @staticmethod
    def _build_tool_error_message(tool_errors: list[str]) -> str:
        combined = " ".join(tool_errors)
        if "Snapshot first" in combined or "Desktop state is empty" in combined:
            return "Nao consegui agir na tela porque faltou uma captura do desktop. Tente pedir uma captura primeiro ou repita a acao."
        if "Either loc or label must be provided" in combined:
            return "A ferramenta recebeu uma acao incompleta. Vou precisar tentar de forma mais especifica, como clicar por coordenadas ou apos uma captura."
        if len(tool_errors) >= 2:
            return "Interrompi a automacao porque as ferramentas do Windows falharam repetidamente nesta tentativa."
        return "A automacao do Windows falhou nesta tentativa. Tente novamente com um pedido mais especifico."
