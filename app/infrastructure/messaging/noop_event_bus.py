from typing import Any


class NoOpEventBus:
    """
    EventBus implementation that intentionally does nothing.

    Production-oriented improvement:
    This is useful for tests, local development, or environments where a broker
    is not required. It still satisfies the EventBus contract, so the workflow
    does not need conditional logic.

    Expansion point:
    Use `EVENT_BUS_PROVIDER=none` to disable broker publication while keeping
    SQLite persistence and WebSocket output active.
    """

    async def publish(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        return

    async def close(self) -> None:
        return
