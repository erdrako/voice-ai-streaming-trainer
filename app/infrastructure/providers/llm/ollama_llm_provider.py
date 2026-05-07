from collections.abc import AsyncIterator
import json

import httpx

from app.application.exceptions import ProviderUnavailableError
from app.config import Settings


SYSTEM_PROMPT = """
Sos un asistente tecnico de entrenamiento para una entrevista backend.
Responde en espanol rioplatense claro, con foco en arquitectura, Python async,
WebSockets, SSE, eventos, baja latencia, cloud, Docker e integraciones locales.
Se concreto y ayuda al usuario a practicar decisiones tecnicas reales.
""".strip()


class OllamaLanguageModelProvider:
    """
    Ollama implementation of the LanguageModelProvider contract.

    Infrastructure responsibility:
    - Know Ollama's `/api/chat` payload shape.
    - Convert Ollama's line-delimited stream into plain text deltas.

    Interchangeability:
    - Add another provider for vLLM, OpenAI, Azure OpenAI, Anthropic, etc.
    - Keep the application use case unchanged as long as text deltas stream.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        """Inject settings and shared HTTP client from the composition root."""

        self.settings = settings
        self.client = client

    async def stream_response(self, conversation: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yield LLM response deltas from Ollama's streaming API."""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *conversation]
        payload = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.3,
            },
        }

        try:
            async with self.client.stream(
                "POST",
                f"{self.settings.ollama_base_url}/api/chat",
                json=payload,
                timeout=self.settings.llm_timeout_seconds,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    event = json.loads(line)
                    content = event.get("message", {}).get("content", "")
                    if content:
                        yield content

                    if event.get("done"):
                        break
        except Exception as exc:
            raise ProviderUnavailableError(
                f"LLM provider failed: {exc}",
                code="LLM_PROVIDER_UNAVAILABLE",
            ) from exc
