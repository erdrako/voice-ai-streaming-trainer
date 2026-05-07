from pathlib import Path


class TemplateSpeechToTextProvider:
    """
    Template implementation for a future STT provider.

    Example future providers:
    - Whisper streaming server
    - Vosk
    - Deepgram
    - Azure Speech
    - Google Speech-to-Text
    - An internal company STT API

    Implementation checklist:
    1. Keep the method signature compatible with SpeechToTextProvider.
    2. Put provider-specific auth/config in `Settings` if needed.
    3. Register this provider in `composition/container.py`.
    4. Add tests using fakes at the application layer and adapter-specific
       tests for provider payload mapping.

    This template is intentionally not wired at runtime.
    """

    async def transcribe_audio(self, audio_path: Path, mime_type: str) -> str:
        raise NotImplementedError("Template implementation for STT transcription.")
