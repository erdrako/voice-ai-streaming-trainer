from dataclasses import dataclass, field


@dataclass
class VoiceSession:
    session_id: str
    audio_buffer: bytearray = field(default_factory=bytearray)
    mime_type: str = "audio/webm"
    conversation: list[dict[str, str]] = field(default_factory=list)

    def start_utterance(self, mime_type: str | None = None) -> None:
        self.audio_buffer.clear()
        if mime_type:
            self.mime_type = mime_type

    def append_audio(self, chunk: bytes) -> None:
        self.audio_buffer.extend(chunk)

    def add_user_text(self, text: str) -> None:
        self.conversation.append({"role": "user", "content": text})

    def add_assistant_text(self, text: str) -> None:
        self.conversation.append({"role": "assistant", "content": text})
