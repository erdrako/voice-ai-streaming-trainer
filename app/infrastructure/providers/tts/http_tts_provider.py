import httpx

from app.application.exceptions import ProviderUnavailableError
from app.config import Settings
from app.infrastructure.resilience.retry import retry_async


class HttpTextToSpeechProvider:
    """
    HTTP adapter for the local Piper TTS service.

    This class implements TextToSpeechProvider. The workflow can synthesize
    speech without knowing that Piper is running behind a Dockerized FastAPI
    service.

    Interchangeability:
    - Add Kokoro, Coqui, Azure, ElevenLabs, Google, or another provider in this
      folder and register it in `composition/container.py`.
    - The use case will still call `synthesize_speech`.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        """Inject settings and shared HTTP client from the composition root."""

        self.settings = settings
        self.client = client

    async def synthesize_speech(self, text: str) -> bytes:
        """Send text to the TTS service and return audio bytes."""

        async def operation() -> bytes:
            response = await self.client.post(
                f"{self.settings.tts_base_url}/synthesize",
                json={"text": text},
                timeout=self.settings.tts_timeout_seconds,
            )
            response.raise_for_status()
            return response.content

        try:
            return await retry_async(
                operation,
                attempts=self.settings.provider_retry_attempts,
                backoff_seconds=self.settings.provider_retry_backoff_seconds,
            )
        except Exception as exc:
            raise ProviderUnavailableError(
                f"TTS provider failed: {exc}",
                code="TTS_PROVIDER_UNAVAILABLE",
            ) from exc
