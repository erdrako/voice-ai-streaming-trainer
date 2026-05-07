import pytest

from app.application.dto.voice_events import ServerEvent
from app.application.use_cases.voice_workflow import VoiceWorkflowUseCase
from app.config import Settings
from app.domain.entities.voice_session import VoiceSession
from app.domain.services.audio_format_service import AudioFormatService
from app.domain.services.segmentation_service import SegmentationService
from app.infrastructure.telemetry.trace import Trace
from app.application.exceptions import ProviderUnavailableError
from tests.fakes import FakeLanguageModelProvider, FakeSpeechToTextProvider, FakeTextToSpeechProvider


class CapturingPublisher:
    """
    Test implementation of EventPublisher.

    This is the same technique used in enterprise tests: replace external
    output adapters with an in-memory fake so the application use case can be
    tested without FastAPI, WebSockets, Redis, or SQLite.
    """

    def __init__(self):
        self.events = []

    async def emit(self, session, event_type, **payload):
        self.events.append({"type": event_type.value, **payload})


class FailingTextToSpeechProvider:
    async def synthesize_speech(self, text):
        raise ProviderUnavailableError("TTS down", code="TTS_PROVIDER_UNAVAILABLE")


def build_use_case(publisher, tts_provider=None):
    settings = Settings(
        event_bus_provider="none",
        database_path="data/test-training.db",
        provider_retry_attempts=1,
    )
    return VoiceWorkflowUseCase(
        settings=settings,
        stt_provider=FakeSpeechToTextProvider(),
        llm_provider=FakeLanguageModelProvider(),
        tts_provider=tts_provider or FakeTextToSpeechProvider(),
        event_publisher=publisher,
        audio_format_service=AudioFormatService(),
        segmentation_service=SegmentationService(),
    )


@pytest.mark.asyncio
async def test_use_case_streams_text_and_synthesizes_segments():
    publisher = CapturingPublisher()
    use_case = build_use_case(publisher)
    session = VoiceSession(session_id="use-case-text")

    await use_case.process_text_message(session, "Que es DI?", Trace())

    event_types = [event["type"] for event in publisher.events]
    assert "ai.response.delta" in event_types
    assert "tts.segment.completed" in event_types
    assert event_types[-1] == ServerEvent.METRICS.value


@pytest.mark.asyncio
async def test_use_case_keeps_text_response_when_tts_fails():
    publisher = CapturingPublisher()
    use_case = build_use_case(publisher, tts_provider=FailingTextToSpeechProvider())
    session = VoiceSession(session_id="use-case-tts-failure")

    await use_case.process_text_message(session, "Que es DI?", Trace())

    event_types = [event["type"] for event in publisher.events]
    errors = [event for event in publisher.events if event["type"] == ServerEvent.ERROR.value]

    assert "ai.response.delta" in event_types
    assert errors
    assert errors[0]["code"] == "TTS_PROVIDER_UNAVAILABLE"
    assert event_types[-1] == ServerEvent.METRICS.value
