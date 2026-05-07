import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    attempts: int,
    backoff_seconds: float,
) -> T:
    """
    Minimal async retry helper for provider calls.

    Production-oriented improvement:
    Provider calls fail in real systems. A small retry/backoff policy makes
    transient network hiccups less likely to break the whole workflow.

    Expansion point:
    - Replace this helper with Tenacity, Polly-like policies, or a circuit
      breaker adapter if the app grows.
    - Keep retry policy at infrastructure boundaries, not inside domain logic.
    """

    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            if attempt < attempts - 1 and backoff_seconds > 0:
                await asyncio.sleep(backoff_seconds * (attempt + 1))

    assert last_error is not None
    raise last_error
