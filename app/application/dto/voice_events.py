from enum import Enum


class ClientEvent(str, Enum):
    """
    Presentation-facing DTO for messages received from the WebSocket client.

    In a .NET layered architecture this would usually live near request DTOs or
    API contracts. It is intentionally not a domain entity: these values describe
    the transport protocol used by the browser, not a business concept.

    Expansion point:
    - Add new client commands here when the browser protocol grows.
    - Keep command handling in the presentation layer thin; delegate workflow
      behavior to application use cases instead of adding business logic there.
    """

    START_UTTERANCE = "start_utterance"
    END_UTTERANCE = "end_utterance"
    TEXT_MESSAGE = "text_message"


class ServerEvent(str, Enum):
    """
    Presentation-facing DTO for messages sent back to the WebSocket client.

    These event names are part of the app's external contract. The application
    layer can ask an injected publisher to emit these events, but it should not
    know whether they travel through FastAPI WebSockets, Server-Sent Events,
    a message broker, or a test fake.

    Expansion point:
    - Add new output events here when the UI needs more visibility.
    - A second output channel, such as SSE or a queue consumer, can implement
      the same publisher contract without changing the workflow use cases.
    """

    SESSION_READY = "session.ready"
    TRANSCRIPTION_STARTED = "transcription.started"
    TRANSCRIPTION_PARTIAL = "transcription.partial"
    TRANSCRIPTION_COMPLETED = "transcription.completed"
    AI_RESPONSE_STARTED = "ai.response.started"
    AI_RESPONSE_DELTA = "ai.response.delta"
    AI_RESPONSE_COMPLETED = "ai.response.completed"
    TTS_STARTED = "tts.started"
    TTS_SEGMENT_COMPLETED = "tts.segment.completed"
    TTS_COMPLETED = "tts.completed"
    METRICS = "metrics"
    ERROR = "error"
