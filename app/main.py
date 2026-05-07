from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4
import base64
from contextlib import asynccontextmanager
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.events import ClientEvent, ServerEvent
from app.services.local_ai_service import LocalAIService
from app.session import VoiceSession, extract_ready_segments, has_speakable_text
from app.telemetry import EventBus, EventStore, Trace


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

settings = get_settings()
event_store = EventStore(settings.database_path)
event_bus = EventBus(settings.redis_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await event_bus.close()


app = FastAPI(title="Voice AI Streaming Trainer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics/recent")
async def recent_metrics() -> list[dict]:
    return event_store.recent_events()


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


async def send_event(
    websocket: WebSocket,
    session: VoiceSession,
    event_type: ServerEvent,
    **payload: str | int | float | dict,
) -> None:
    event = {"type": event_type.value, **payload}
    await websocket.send_json(event)
    stored_payload = sanitize_payload(payload)
    event_store.record_event(session.session_id, event_type.value, stored_payload)
    await event_bus.publish(session.session_id, event_type.value, stored_payload)


def sanitize_payload(payload: dict) -> dict:
    sanitized = dict(payload)
    audio = sanitized.pop("audio", None)
    if isinstance(audio, str):
        sanitized["audio_base64_chars"] = len(audio)
    return sanitized


def audio_suffix(mime_type: str) -> str:
    if "mp4" in mime_type:
        return ".mp4"
    if "mpeg" in mime_type or "mp3" in mime_type:
        return ".mp3"
    if "wav" in mime_type:
        return ".wav"
    return ".webm"


async def process_text(
    websocket: WebSocket,
    session: VoiceSession,
    service: LocalAIService,
    text: str,
    trace: Trace,
) -> None:
    session.add_user_text(text)
    await send_event(websocket, session, ServerEvent.AI_RESPONSE_STARTED)

    full_response = ""
    segment_buffer = ""
    segment_index = 0
    async for delta in service.stream_response(session.conversation):
        full_response += delta
        segment_buffer += delta
        if "llm_first_token_ms" not in trace.marks:
            trace.mark("llm_first_token_ms")
        await send_event(websocket, session, ServerEvent.AI_RESPONSE_DELTA, text=delta)

        ready_segments, segment_buffer = extract_ready_segments(segment_buffer)
        for segment in ready_segments:
            if not has_speakable_text(segment):
                continue
            segment_index += 1
            await synthesize_segment(websocket, session, service, segment, segment_index)

    session.add_assistant_text(full_response)
    trace.mark("llm_completed_ms")
    await send_event(websocket, session, ServerEvent.AI_RESPONSE_COMPLETED)

    remaining_segment = segment_buffer.strip()
    if has_speakable_text(remaining_segment):
        segment_index += 1
        await synthesize_segment(websocket, session, service, remaining_segment, segment_index)

    trace.mark("workflow_completed_ms")
    await send_event(websocket, session, ServerEvent.TTS_COMPLETED, segments=segment_index)
    await send_event(websocket, session, ServerEvent.METRICS, metrics=trace.snapshot())


async def synthesize_segment(
    websocket: WebSocket,
    session: VoiceSession,
    service: LocalAIService,
    text: str,
    segment_index: int,
) -> None:
    await send_event(websocket, session, ServerEvent.TTS_STARTED, segment=segment_index)
    speech = await service.synthesize_speech(text)
    audio = base64.b64encode(speech).decode("ascii")
    await send_event(
        websocket,
        session,
        ServerEvent.TTS_SEGMENT_COMPLETED,
        segment=segment_index,
        text=text,
        audio=audio,
        mime_type="audio/wav",
    )


async def process_audio(
    websocket: WebSocket,
    session: VoiceSession,
    service: LocalAIService,
    trace: Trace,
) -> None:
    if not session.audio_buffer:
        await send_event(websocket, session, ServerEvent.ERROR, message="No llego audio para transcribir.")
        return

    suffix = audio_suffix(session.mime_type)
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(session.audio_buffer)
        temp_path = Path(temp_audio.name)

    try:
        await send_event(websocket, session, ServerEvent.TRANSCRIPTION_STARTED)
        text = await service.transcribe_audio(temp_path, session.mime_type)
        trace.mark("transcription_completed_ms")
        await send_event(websocket, session, ServerEvent.TRANSCRIPTION_COMPLETED, text=text)
        await process_text(websocket, session, service, text, trace)
    finally:
        temp_path.unlink(missing_ok=True)


async def maybe_send_partial_transcription(
    websocket: WebSocket,
    session: VoiceSession,
    service: LocalAIService,
) -> None:
    settings = get_settings()
    enough_audio = len(session.audio_buffer) >= settings.partial_transcription_min_bytes
    enough_chunks = (
        session.audio_chunks_received - session.last_partial_chunk
        >= settings.partial_transcription_every_chunks
    )
    if not enough_audio or not enough_chunks:
        return

    session.last_partial_chunk = session.audio_chunks_received
    suffix = audio_suffix(session.mime_type)
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(session.audio_buffer)
        temp_path = Path(temp_audio.name)

    try:
        text = await service.transcribe_audio(temp_path, session.mime_type)
        if text:
            await send_event(websocket, session, ServerEvent.TRANSCRIPTION_PARTIAL, text=text)
    finally:
        temp_path.unlink(missing_ok=True)


@app.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    session = VoiceSession(session_id=session_id or str(uuid4()))
    service = LocalAIService(get_settings())
    event_store.create_session(session.session_id)

    await send_event(websocket, session, ServerEvent.SESSION_READY, session_id=session.session_id)

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                session.append_audio(message["bytes"])
                await maybe_send_partial_transcription(websocket, session, service)
                continue

            if "text" not in message or not message["text"]:
                continue

            data = json.loads(message["text"])
            event_type = data.get("type")

            if event_type == ClientEvent.START_UTTERANCE:
                session.start_utterance(data.get("mime_type"))
            elif event_type == ClientEvent.END_UTTERANCE:
                await process_audio(websocket, session, service, Trace())
            elif event_type == ClientEvent.TEXT_MESSAGE:
                text = str(data.get("text", "")).strip()
                if text:
                    await process_text(websocket, session, service, text, Trace())
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await send_event(websocket, session, ServerEvent.ERROR, message=str(exc))
    finally:
        await service.close()
