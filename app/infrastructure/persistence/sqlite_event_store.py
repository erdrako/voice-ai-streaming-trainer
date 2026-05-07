import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class SqliteEventStore:
    """
    SQLite implementation of the EventStore contract.

    Infrastructure responsibility:
    - Know how to talk to SQLite.
    - Hide SQL schema and connection details from application use cases.

    Interchangeability:
    - If SQLite becomes insufficient, add a new adapter such as
      `PostgresEventStore` in this same folder.
    - As long as the new adapter satisfies `EventStore`, no use case changes.
    - Register the replacement in `composition/container.py`.
    """

    def __init__(self, database_path: str):
        """
        Variables:
        - `database_path`: filesystem path for the local training database.
          In Docker this points to `/data/training.db`; outside Docker it
          defaults to `data/training.db`.
        """

        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Create a short-lived SQLite connection for one operation."""

        return sqlite3.connect(self.database_path)

    def _init_db(self) -> None:
        """Create the tiny persistence schema used by the training app."""

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def create_session(self, session_id: str) -> None:
        """Persist a session row if it does not exist yet."""

        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO sessions (session_id, created_at) VALUES (?, ?)",
                (session_id, time.time()),
            )

    def record_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """
        Persist one sanitized event payload.

        Note:
        - Audio bytes/base64 should be sanitized before this method is called.
        - The store records diagnostic metadata, not heavy binary artifacts.
        """

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO events (session_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, event_type, json.dumps(payload), time.time()),
            )

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent events for debugging, docs demos, and interview walkthroughs."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT session_id, event_type, payload, created_at
                FROM events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "session_id": row[0],
                "event_type": row[1],
                "payload": json.loads(row[2]),
                "created_at": row[3],
            }
            for row in rows
        ]
