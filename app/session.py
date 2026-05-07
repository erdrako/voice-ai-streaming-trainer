from dataclasses import dataclass, field
import re
import time


@dataclass
class VoiceSession:
    session_id: str
    audio_buffer: bytearray = field(default_factory=bytearray)
    mime_type: str = "audio/webm"
    conversation: list[dict[str, str]] = field(default_factory=list)
    audio_chunks_received: int = 0
    last_partial_chunk: int = 0
    created_at: float = field(default_factory=time.perf_counter)

    def start_utterance(self, mime_type: str | None = None) -> None:
        self.audio_buffer.clear()
        self.audio_chunks_received = 0
        self.last_partial_chunk = 0
        if mime_type:
            self.mime_type = mime_type

    def append_audio(self, chunk: bytes) -> None:
        self.audio_buffer.extend(chunk)
        self.audio_chunks_received += 1

    def add_user_text(self, text: str) -> None:
        self.conversation.append({"role": "user", "content": text})

    def add_assistant_text(self, text: str) -> None:
        self.conversation.append({"role": "assistant", "content": text})


def extract_ready_segments(buffer: str) -> tuple[list[str], str]:
    matches = list(re.finditer(r"[^.!?\n]+[.!?\n]+", buffer))
    if not matches:
        return [], buffer

    last_end = matches[-1].end()
    segments = [match.group(0).strip() for match in matches if match.group(0).strip()]
    return segments, buffer[last_end:]


def has_speakable_text(text: str) -> bool:
    return bool(re.search(r"[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]", text))
