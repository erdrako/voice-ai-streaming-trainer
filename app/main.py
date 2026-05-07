from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4
import base64
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.events import ClientEvent, ServerEvent
from app.services.local_ai_service import LocalAIService
from app.session import VoiceSession


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Voice AI Streaming Trainer")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


async def send_event(websocket: WebSocket, event_type: ServerEvent, **payload: str) -> None:
    await websocket.send_json({"type": event_type.value, **payload})


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
) -> None:
    session.add_user_text(text)
    await send_event(websocket, ServerEvent.AI_RESPONSE_STARTED)

    full_response = ""
    async for delta in service.stream_response(session.conversation):
        full_response += delta
        await send_event(websocket, ServerEvent.AI_RESPONSE_DELTA, text=delta)

    session.add_assistant_text(full_response)
    await send_event(websocket, ServerEvent.AI_RESPONSE_COMPLETED)

    if full_response.strip():
        await send_event(websocket, ServerEvent.TTS_STARTED)
        speech = await service.synthesize_speech(full_response)
        audio = base64.b64encode(speech).decode("ascii")
        await send_event(websocket, ServerEvent.TTS_COMPLETED, audio=audio, mime_type="audio/wav")


async def process_audio(
    websocket: WebSocket,
    session: VoiceSession,
    service: LocalAIService,
) -> None:
    if not session.audio_buffer:
        await send_event(websocket, ServerEvent.ERROR, message="No llego audio para transcribir.")
        return

    suffix = audio_suffix(session.mime_type)
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(session.audio_buffer)
        temp_path = Path(temp_audio.name)

    try:
        await send_event(websocket, ServerEvent.TRANSCRIPTION_STARTED)
        text = await service.transcribe_audio(temp_path, session.mime_type)
        await send_event(websocket, ServerEvent.TRANSCRIPTION_COMPLETED, text=text)
        await process_text(websocket, session, service, text)
    finally:
        temp_path.unlink(missing_ok=True)


@app.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    session = VoiceSession(session_id=session_id or str(uuid4()))
    service = LocalAIService(get_settings())

    await send_event(websocket, ServerEvent.SESSION_READY, session_id=session.session_id)

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                session.append_audio(message["bytes"])
                continue

            if "text" not in message or not message["text"]:
                continue

            data = json.loads(message["text"])
            event_type = data.get("type")

            if event_type == ClientEvent.START_UTTERANCE:
                session.start_utterance(data.get("mime_type"))
            elif event_type == ClientEvent.END_UTTERANCE:
                await process_audio(websocket, session, service)
            elif event_type == ClientEvent.TEXT_MESSAGE:
                text = str(data.get("text", "")).strip()
                if text:
                    await process_text(websocket, session, service, text)
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await send_event(websocket, ServerEvent.ERROR, message=str(exc))
    finally:
        await service.close()
