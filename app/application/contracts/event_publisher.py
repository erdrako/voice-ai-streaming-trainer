from typing import Any, Protocol

from app.application.dto.voice_events import ServerEvent
from app.domain.entities.voice_session import VoiceSession


class EventPublisher(Protocol):
    """
    Application output port for workflow events.

    The use cases call this contract instead of calling FastAPI's WebSocket
    directly. That is responsibility delegation: presentation owns transport,
    application owns orchestration, infrastructure owns persistence/brokers.

    Expansion point:
    - `WebSocketEventPublisher` is the active implementation.
    - A future `SseEventPublisher`, `ConsoleEventPublisher`, or
      `QueuedEventPublisher` can implement this same contract.
    """

    async def emit(
        self,
        session: VoiceSession,
        event_type: ServerEvent,
        **payload: Any,
    ) -> None:
        """Emit a workflow event to the active output channel."""
