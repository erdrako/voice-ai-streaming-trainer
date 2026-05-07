from pathlib import Path
from typing import Protocol


class SpeechToTextProvider(Protocol):
    """
    Application contract for speech-to-text providers.

    This is the Dependency Inversion Principle in practice: use cases depend on
    this contract, not on faster-whisper, HTTPX, Docker service URLs, or any
    provider-specific SDK. If the current STT implementation is wrong, slow, or
    not accurate enough, the application workflow does not need to change.

    Expansion point:
    - Add a new implementation under `app/infrastructure/providers/stt/`.
    - Use `template_stt_provider.py` as a guide for the required shape.
    - Register the new concrete class in `app/composition/container.py`.
    """

    async def transcribe_audio(self, audio_path: Path, mime_type: str) -> str:
        """Convert an audio file into text for the active voice workflow."""
