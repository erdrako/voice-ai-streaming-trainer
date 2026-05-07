from pathlib import Path

import httpx

from app.application.exceptions import ProviderUnavailableError
from app.config import Settings
from app.infrastructure.resilience.retry import retry_async


class HttpSpeechToTextProvider:
    """
    HTTP adapter for the local faster-whisper STT service.

    This class implements the SpeechToTextProvider contract. The application
    layer sees only `transcribe_audio`; it does not know this call goes over
    HTTP to a Docker service.

    Interchangeability:
    - Replace this with an SDK-based provider, a cloud STT provider, or a
      streaming STT provider by implementing the same contract.
    - Register the replacement in `composition/container.py`.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        """
        Dependency Injection:
        - `settings` provides configuration.
        - `client` is injected so connection lifetime is managed by the
          composition root, not by each method call.
        """

        self.settings = settings
        self.client = client

    async def transcribe_audio(self, audio_path: Path, mime_type: str) -> str:
        """Send an audio file to the STT service and return normalized text."""

        async def operation() -> str:
            with audio_path.open("rb") as audio_file:
                files = {"file": (audio_path.name, audio_file, mime_type)}
                response = await self.client.post(
                    f"{self.settings.stt_base_url}/transcribe",
                    files=files,
                    timeout=self.settings.stt_timeout_seconds,
                )
            response.raise_for_status()
            return response.json()["text"].strip()

        try:
            return await retry_async(
                operation,
                attempts=self.settings.provider_retry_attempts,
                backoff_seconds=self.settings.provider_retry_backoff_seconds,
            )
        except Exception as exc:
            raise ProviderUnavailableError(
                f"STT provider failed: {exc}",
                code="STT_PROVIDER_UNAVAILABLE",
            ) from exc
