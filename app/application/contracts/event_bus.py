from typing import Any, Protocol


class EventBus(Protocol):
    """
    Application contract for internal event publication.

    Redis is only one implementation detail. The application wants to publish
    events for observability or future workers; it should not care whether the
    actual bus is Redis Streams, Kafka, RabbitMQ, NATS, SQS, or a no-op fake.

    Expansion point:
    - Add a new adapter under `app/infrastructure/messaging/`.
    - Keep publishes best-effort unless the workflow explicitly requires
      delivery guarantees.
    """

    async def publish(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a sanitized workflow event to an internal event stream."""

    async def close(self) -> None:
        """Release network resources held by the event bus implementation."""
