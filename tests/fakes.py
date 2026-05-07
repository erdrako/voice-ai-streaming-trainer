class FakeLocalAIService:
    instances = []

    def __init__(self, settings):
        self.settings = settings
        self.closed = False
        FakeLocalAIService.instances.append(self)

    async def close(self):
        self.closed = True

    async def transcribe_audio(self, audio_path, mime_type):
        assert audio_path.exists()
        assert mime_type
        return "Explica WebSockets en una frase."

    async def stream_response(self, conversation):
        assert conversation[-1]["role"] == "user"
        for delta in ["Un WebSocket ", "mantiene una conexion ", "bidireccional. ", "Sirve para tiempo real."]:
            yield delta

    async def synthesize_speech(self, text):
        return f"RIFFfake-wav-{text}".encode()
