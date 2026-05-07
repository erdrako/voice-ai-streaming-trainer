from collections.abc import AsyncIterator
from pathlib import Path
import json

import httpx

from app.config import Settings


SYSTEM_PROMPT = """
Sos un asistente tecnico de entrenamiento para una entrevista backend.
Responde en espanol rioplatense claro, con foco en arquitectura, Python async,
WebSockets, SSE, eventos, baja latencia, cloud, Docker e integraciones locales.
Se concreto y ayuda al usuario a practicar decisiones tecnicas reales.
""".strip()


class LocalAIService:
    def __init__(self, settings: Settings):
        timeout = httpx.Timeout(settings.request_timeout_seconds)
        self.settings = settings
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self.client.aclose()

    async def transcribe_audio(self, audio_path: Path, mime_type: str) -> str:
        with audio_path.open("rb") as audio_file:
            files = {"file": (audio_path.name, audio_file, mime_type)}
            response = await self.client.post(
                f"{self.settings.stt_base_url}/transcribe",
                files=files,
            )
        response.raise_for_status()
        return response.json()["text"].strip()

    async def stream_response(self, conversation: list[dict[str, str]]) -> AsyncIterator[str]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *conversation]
        payload = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.3,
            },
        }

        async with self.client.stream(
            "POST",
            f"{self.settings.ollama_base_url}/api/chat",
            json=payload,
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

    async def synthesize_speech(self, text: str) -> bytes:
        response = await self.client.post(
            f"{self.settings.tts_base_url}/synthesize",
            json={"text": text},
        )
        response.raise_for_status()
        return response.content
