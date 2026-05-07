from enum import Enum


class ClientEvent(str, Enum):
    START_UTTERANCE = "start_utterance"
    END_UTTERANCE = "end_utterance"
    TEXT_MESSAGE = "text_message"


class ServerEvent(str, Enum):
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
