from typing import Any

from fastapi import WebSocket

from app.application.contracts.event_bus import EventBus
from app.application.contracts.event_store import EventStore
from app.application.dto.voice_events import ServerEvent
from app.domain.entities.voice_session import VoiceSession


class WebSocketEventPublisher:
    """
    Presentation adapter for the EventPublisher output port.

    Responsibilities:
    - Send workflow events to the active FastAPI WebSocket.
    - Persist sanitized events through EventStore.
    - Publish sanitized events through EventBus.

    This class is intentionally outside the application layer because FastAPI's
    WebSocket is a transport detail. The application use case calls only the
    EventPublisher contract.

    Expansion point:
    - Add `SseEventPublisher` if the UI moves to Server-Sent Events.
    - Add `QueuedEventPublisher` if another service should consume results.
    - Keep payload sanitization here so stores/brokers do not receive heavy
      audio blobs.
    """

    def __init__(
        self,
        websocket: WebSocket,
        event_store: EventStore,
        event_bus: EventBus,
    ):
        """
        Dependency Injection:
        - FastAPI creates the WebSocket.
        - The composition root creates EventStore/EventBus.
        - This adapter combines them for a single session connection.
        """

        self.websocket = websocket
        self.event_store = event_store
        self.event_bus = event_bus

    async def emit(
        self,
        session: VoiceSession,
        event_type: ServerEvent,
        **payload: Any,
    ) -> None:
        """Send to client, then record and publish sanitized diagnostics."""

        event = {"type": event_type.value, **payload}
        await self.websocket.send_json(event)
        stored_payload = sanitize_payload(payload)
        self.event_store.record_event(session.session_id, event_type.value, stored_payload)
        await self.event_bus.publish(session.session_id, event_type.value, stored_payload)


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Remove large audio payloads before persistence/broker publication.

    Variable guide:
    - `payload`: original event data intended for the browser.
    - `audio`: base64 string needed by the browser but too noisy for SQLite.
    - `audio_base64_chars`: diagnostic size marker kept for observability.
    """

    sanitized = dict(payload)
    audio = sanitized.pop("audio", None)
    if isinstance(audio, str):
        sanitized["audio_base64_chars"] = len(audio)
    return sanitized
