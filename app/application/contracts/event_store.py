from typing import Any, Protocol


class EventStore(Protocol):
    """
    Application contract for session/event persistence.

    SQLite is the current persistence adapter because it is simple for local
    training. The application only needs to create sessions, record events, and
    inspect recent events, so those are the only operations exposed.

    Expansion point:
    - Add PostgreSQL, MongoDB, Elastic, BigQuery, or another store under
      `app/infrastructure/persistence/`.
    - Register the new implementation in the composition root.
    - Keep this contract small so persistence details do not leak upward.
    """

    def create_session(self, session_id: str) -> None:
        """Persist that a voice session exists."""

    def record_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Persist one sanitized event emitted by the workflow."""

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent events for diagnostics and interview demos."""
