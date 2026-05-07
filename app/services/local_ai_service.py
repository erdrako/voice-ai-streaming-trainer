"""
Backward-compatible facade for the old combined AI service.

New enterprise-style code uses three explicit provider contracts instead:
- SpeechToTextProvider
- LanguageModelProvider
- TextToSpeechProvider

This facade is kept only as a transition aid for older notes. New code should
prefer the concrete providers under `app.infrastructure.providers.*`.
"""

import httpx

from app.config import Settings
from app.infrastructure.providers.llm.ollama_llm_provider import OllamaLanguageModelProvider
from app.infrastructure.providers.stt.http_stt_provider import HttpSpeechToTextProvider
from app.infrastructure.providers.tts.http_tts_provider import HttpTextToSpeechProvider


class LocalAIService:
    """
    Transitional facade that delegates to the segregated providers.

    Expansion note:
    If this project were production code, this class could be deleted after all
    callers migrate to the separate contracts. It remains here to make the
    refactor easier to compare with the previous implementation.
    """

    def __init__(self, settings: Settings):
        timeout = httpx.Timeout(settings.request_timeout_seconds)
        self.client = httpx.AsyncClient(timeout=timeout)
        self.stt = HttpSpeechToTextProvider(settings, self.client)
        self.llm = OllamaLanguageModelProvider(settings, self.client)
        self.tts = HttpTextToSpeechProvider(settings, self.client)

    async def close(self) -> None:
        await self.client.aclose()

    async def transcribe_audio(self, audio_path, mime_type: str) -> str:
        return await self.stt.transcribe_audio(audio_path, mime_type)

    async def stream_response(self, conversation):
        async for delta in self.llm.stream_response(conversation):
            yield delta

    async def synthesize_speech(self, text: str) -> bytes:
        return await self.tts.synthesize_speech(text)
