from typing import Any


class TemplateEventBus:
    """
    Template implementation for a future message broker.

    Use this when adding Kafka, RabbitMQ, NATS, SQS, Azure Service Bus, or
    Google Pub/Sub. The workflow already depends on the EventBus contract, so a
    new broker only needs to match this shape and be registered in the container.

    This template is intentionally not wired at runtime.
    """

    async def publish(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError("Template implementation for event bus publish.")

    async def close(self) -> None:
        raise NotImplementedError("Template implementation for event bus cleanup.")
