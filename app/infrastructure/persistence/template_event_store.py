from typing import Any


class TemplateEventStore:
    """
    Template implementation for a future persistence provider.

    Use this as a checklist when replacing SQLite with PostgreSQL, MongoDB,
    Elastic, BigQuery, or another storage technology.

    Implementation steps:
    1. Copy this class to a provider-specific file, for example
       `postgres_event_store.py`.
    2. Replace the method bodies with real database calls.
    3. Keep the public method signatures compatible with EventStore.
    4. Register the new class in `composition/container.py`.

    This template is intentionally not wired at runtime.
    """

    def create_session(self, session_id: str) -> None:
        raise NotImplementedError("Template implementation for session persistence.")

    def record_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError("Template implementation for event persistence.")

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        raise NotImplementedError("Template implementation for querying recent events.")
