class FakeSpeechToTextProvider:
    """
    Test fake for the STT contract.

    This fake demonstrates why dependency injection helps testing: the use case
    can validate orchestration without starting faster-whisper or Docker.
    """

    async def transcribe_audio(self, audio_path, mime_type):
        assert audio_path.exists()
        assert mime_type
        return "Explica WebSockets en una frase."


class FakeLanguageModelProvider:
    """
    Test fake for the LLM contract.

    It yields deterministic deltas so WebSocket and use-case tests can assert
    exact event ordering.
    """

    async def stream_response(self, conversation):
        assert conversation[-1]["role"] == "user"
        for delta in ["Un WebSocket ", "mantiene una conexion ", "bidireccional. ", "Sirve para tiempo real."]:
            yield delta


class FakeTextToSpeechProvider:
    """
    Test fake for the TTS contract.

    A real TTS provider returns audio bytes. The fake returns deterministic
    bytes that are still base64-encoded by the workflow.
    """

    async def synthesize_speech(self, text):
        return f"RIFFfake-wav-{text}".encode()
