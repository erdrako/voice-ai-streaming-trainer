from dataclasses import dataclass, field
import time


@dataclass
class VoiceSession:
    """
    Domain entity representing one interactive voice session.

    This class is deliberately free of FastAPI, HTTPX, Redis, SQLite, Docker,
    and provider-specific dependencies. That makes it easy to test and reuse.
    In .NET terms, this is closer to a Domain.Entity project than to WebApi or
    Infrastructure.Repository.

    Variable guide:
    - `session_id`: stable identifier for this WebSocket conversation.
    - `audio_buffer`: accumulated audio bytes for the current utterance.
    - `mime_type`: browser-provided audio type used when creating temp files.
    - `conversation`: chat history passed to the LLM provider.
    - `audio_chunks_received`: count used to decide when partial STT is useful.
    - `last_partial_chunk`: last chunk index that triggered partial STT.
    - `created_at`: monotonic timestamp for diagnostic use.

    Expansion point:
    - If sessions become persistent domain objects, add a repository contract
      in `application/contracts/` and a concrete adapter in infrastructure.
    """

    session_id: str
    audio_buffer: bytearray = field(default_factory=bytearray)
    mime_type: str = "audio/webm"
    conversation: list[dict[str, str]] = field(default_factory=list)
    audio_chunks_received: int = 0
    last_partial_chunk: int = 0
    created_at: float = field(default_factory=time.perf_counter)

    def start_utterance(self, mime_type: str | None = None) -> None:
        """
        Reset transient audio state for a new user utterance.

        Responsibility delegation:
        - The entity owns its own state transitions.
        - The WebSocket handler only decides when this method should be called.
        """

        self.audio_buffer.clear()
        self.audio_chunks_received = 0
        self.last_partial_chunk = 0
        if mime_type:
            self.mime_type = mime_type

    def append_audio(self, chunk: bytes) -> None:
        """Add one browser audio chunk to the current utterance buffer."""

        self.audio_buffer.extend(chunk)
        self.audio_chunks_received += 1

    def add_user_text(self, text: str) -> None:
        """Append a user message in the role format expected by LLM providers."""

        self.conversation.append({"role": "user", "content": text})

    def add_assistant_text(self, text: str) -> None:
        """Append the assistant response so the next turn has conversation memory."""

        self.conversation.append({"role": "assistant", "content": text})
