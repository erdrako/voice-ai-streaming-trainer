from typing import Protocol


class TextToSpeechProvider(Protocol):
    """
    Application contract for text-to-speech providers.

    This abstraction makes Piper replaceable. For example, if Piper produces
    poor voice quality for a use case, you could add Kokoro, Coqui, Azure Speech,
    ElevenLabs, Google Cloud TTS, or an internal TTS service without rewriting
    the orchestration use case.

    Expansion point:
    - Add a new implementation under `app/infrastructure/providers/tts/`.
    - Use `template_tts_provider.py` as the checklist for a future provider.
    - Wire the new provider in `app/composition/container.py`.
    """

    async def synthesize_speech(self, text: str) -> bytes:
        """Return WAV/encoded audio bytes for the provided text segment."""
