import asyncio
import json
from typing import Any

from redis.asyncio import Redis


class RedisEventBus:
    """
    Redis Streams implementation of the EventBus contract.

    Infrastructure responsibility:
    - Know how to publish to Redis.
    - Hide Redis client details from the application workflow.

    Interchangeability:
    - If the team uses Kafka/RabbitMQ/NATS/SQS, add another adapter in this
      folder and register it in `composition/container.py`.
    - The use cases should still call only `EventBus.publish`.
    """

    def __init__(self, redis_url: str | None):
        """
        Variables:
        - `redis_url`: connection string. If it is None/empty, the bus becomes
          a no-op style adapter and silently skips publishes.
        - `client`: concrete Redis client. Kept private to this infrastructure
          adapter so it does not leak into application code.
        """

        self.redis_url = redis_url
        self.client: Redis | None = Redis.from_url(redis_url) if redis_url else None

    async def publish(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """
        Publish a sanitized event to the `voice_ai_events` stream.

        The publish is best-effort and has a short timeout because observability
        should not block the user's voice workflow in this training app.
        """

        if not self.client:
            return

        try:
            await asyncio.wait_for(
                self.client.xadd(
                    "voice_ai_events",
                    {
                        "session_id": session_id,
                        "event_type": event_type,
                        "payload": json.dumps(payload),
                    },
                    maxlen=1000,
                    approximate=True,
                ),
                timeout=0.05,
            )
        except Exception:
            return

    async def close(self) -> None:
        """Close the underlying Redis connection when FastAPI shuts down."""

        if self.client:
            await self.client.aclose()
