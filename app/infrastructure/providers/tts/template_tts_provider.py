class TemplateTextToSpeechProvider:
    """
    Template implementation for a future TTS provider.

    Example future providers:
    - Kokoro
    - Coqui
    - Azure Speech
    - ElevenLabs
    - Google Cloud TTS
    - A company-internal voice service

    Implementation checklist:
    1. Keep the method signature compatible with TextToSpeechProvider.
    2. Return audio bytes in a format the presentation layer can label.
    3. Add provider-specific config to `Settings`.
    4. Register the new provider in `composition/container.py`.
    5. Keep TTS segmentation in the domain service, not in this adapter.

    This template is intentionally not wired at runtime.
    """

    async def synthesize_speech(self, text: str) -> bytes:
        raise NotImplementedError("Template implementation for TTS synthesis.")
