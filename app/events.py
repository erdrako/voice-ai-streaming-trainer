"""
Backward-compatible import location for voice event DTOs.

The refactor moved event DTOs to `app.application.dto.voice_events` because
they are application/presentation contracts rather than domain entities.
Keeping this re-export avoids breaking older tests or notes while you study the
new layered layout.
"""

from app.application.dto.voice_events import ClientEvent, ServerEvent

__all__ = ["ClientEvent", "ServerEvent"]
