from dataclasses import dataclass, field
import json
import sqlite3
import time
import asyncio
from pathlib import Path
from typing import Any

from redis.asyncio import Redis


@dataclass
class Trace:
    started_at: float = field(default_factory=time.perf_counter)
    marks: dict[str, float] = field(default_factory=dict)

    def mark(self, name: str) -> None:
        self.marks[name] = round((time.perf_counter() - self.started_at) * 1000, 2)

    def snapshot(self) -> dict[str, float]:
        return dict(self.marks)


class EventStore:
    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _init_db(self) -> None:
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
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO sessions (session_id, created_at) VALUES (?, ?)",
                (session_id, time.time()),
            )

    def record_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO events (session_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, event_type, json.dumps(payload), time.time()),
            )

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
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


class EventBus:
    def __init__(self, redis_url: str | None):
        self.redis_url = redis_url
        self.client: Redis | None = Redis.from_url(redis_url) if redis_url else None

    async def publish(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
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
        if self.client:
            await self.client.aclose()
