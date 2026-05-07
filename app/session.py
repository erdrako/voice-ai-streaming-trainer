"""
Backward-compatible import location for session and segmentation helpers.

The refactor moved these concepts into the domain layer:
- `VoiceSession` -> `app.domain.entities.voice_session`
- segmentation helpers -> `app.domain.services.segmentation_service`

This file preserves older imports while the documentation teaches the new
enterprise-style structure.
"""

from app.domain.entities.voice_session import VoiceSession
from app.domain.services.segmentation_service import SegmentationService

_segmentation_service = SegmentationService()


def extract_ready_segments(buffer: str) -> tuple[list[str], str]:
    return _segmentation_service.extract_ready_segments(buffer)


def has_speakable_text(text: str) -> bool:
    return _segmentation_service.has_speakable_text(text)


__all__ = ["VoiceSession", "extract_ready_segments", "has_speakable_text"]
