from fastapi.testclient import TestClient

from app.main import app, container
from tests.fakes import (
    FakeLanguageModelProvider,
    FakeSpeechToTextProvider,
    FakeTextToSpeechProvider,
)


def install_fake_providers():
    container.stt_provider = FakeSpeechToTextProvider()
    container.llm_provider = FakeLanguageModelProvider()
    container.tts_provider = FakeTextToSpeechProvider()


def test_text_message_streams_llm_and_returns_tts(monkeypatch):
    install_fake_providers()

    client = TestClient(app)

    with client.websocket_connect("/ws/session/test-text") as websocket:
        assert websocket.receive_json()["type"] == "session.ready"

        websocket.send_json({"type": "text_message", "text": "Que es un WebSocket?"})

        events = []
        while True:
            event = websocket.receive_json()
            events.append(event)
            if event["type"] == "tts.completed":
                events.append(websocket.receive_json())
                break

    event_types = [event["type"] for event in events]
    assert event_types == [
        "ai.response.started",
        "ai.response.delta",
        "ai.response.delta",
        "ai.response.delta",
        "tts.started",
        "tts.segment.completed",
        "ai.response.delta",
        "tts.started",
        "tts.segment.completed",
        "ai.response.completed",
        "tts.completed",
        "metrics",
    ]
    segment_events = [event for event in events if event["type"] == "tts.segment.completed"]
    assert len(segment_events) == 2
    assert segment_events[0]["mime_type"] == "audio/wav"
    assert segment_events[0]["audio"]


def test_audio_message_transcribes_then_streams_response(monkeypatch):
    install_fake_providers()

    client = TestClient(app)

    with client.websocket_connect("/ws/session/test-audio") as websocket:
        assert websocket.receive_json()["type"] == "session.ready"

        websocket.send_json({"type": "start_utterance", "mime_type": "audio/wav"})
        websocket.send_bytes(b"fake audio")
        websocket.send_json({"type": "end_utterance"})

        events = []
        while True:
            event = websocket.receive_json()
            events.append(event)
            if event["type"] == "tts.completed":
                events.append(websocket.receive_json())
                break

    event_types = [event["type"] for event in events]
    assert event_types[:2] == ["transcription.started", "transcription.completed"]
    assert "ai.response.completed" in event_types
    assert "tts.completed" in event_types
    assert "metrics" in event_types
    assert events[1]["text"] == "Explica WebSockets en una frase."
