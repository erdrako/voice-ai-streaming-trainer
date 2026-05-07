from fastapi.testclient import TestClient

from app.main import app
from tests.fakes import FakeLocalAIService


def test_text_message_streams_llm_and_returns_tts(monkeypatch):
    FakeLocalAIService.instances.clear()
    monkeypatch.setattr("app.main.LocalAIService", FakeLocalAIService)

    client = TestClient(app)

    with client.websocket_connect("/ws/session/test-text") as websocket:
        assert websocket.receive_json()["type"] == "session.ready"

        websocket.send_json({"type": "text_message", "text": "Que es un WebSocket?"})

        events = []
        while True:
            event = websocket.receive_json()
            events.append(event)
            if event["type"] == "tts.completed":
                break

    assert [event["type"] for event in events] == [
        "ai.response.started",
        "ai.response.delta",
        "ai.response.delta",
        "ai.response.delta",
        "ai.response.completed",
        "tts.started",
        "tts.completed",
    ]
    assert events[-1]["mime_type"] == "audio/wav"
    assert events[-1]["audio"]
    assert FakeLocalAIService.instances[-1].closed


def test_audio_message_transcribes_then_streams_response(monkeypatch):
    FakeLocalAIService.instances.clear()
    monkeypatch.setattr("app.main.LocalAIService", FakeLocalAIService)

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
                break

    event_types = [event["type"] for event in events]
    assert event_types[:2] == ["transcription.started", "transcription.completed"]
    assert "ai.response.completed" in event_types
    assert "tts.completed" in event_types
    assert events[1]["text"] == "Explica WebSockets en una frase."
