from uuid import uuid4
import json

from fastapi import WebSocket, WebSocketDisconnect

from app.application.dto.voice_events import ClientEvent, ServerEvent
from app.composition.container import AppContainer
from app.domain.entities.voice_session import VoiceSession
from app.infrastructure.telemetry.trace import Trace
from app.presentation.websocket.event_publisher import WebSocketEventPublisher


async def handle_voice_session(
    websocket: WebSocket,
    session_id: str,
    container: AppContainer,
) -> None:
    """
    Presentation-layer WebSocket handler.

    This function owns transport concerns:
    - Accepting the WebSocket.
    - Parsing JSON/browser binary frames.
    - Translating client events into use case calls.
    - Handling disconnects.

    Responsibility delegation:
    The workflow itself is delegated to VoiceWorkflowUseCase created by the
    container. This is the same idea as a .NET controller delegating to an
    injected application service.
    """

    await websocket.accept()
    session = VoiceSession(session_id=session_id or str(uuid4()))
    container.event_store.create_session(session.session_id)

    publisher = WebSocketEventPublisher(
        websocket=websocket,
        event_store=container.event_store,
        event_bus=container.event_bus,
    )
    workflow = container.create_voice_workflow(publisher)

    await publisher.emit(session, ServerEvent.SESSION_READY, session_id=session.session_id)

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                await workflow.handle_audio_chunk(session, message["bytes"])
                continue

            if "text" not in message or not message["text"]:
                continue

            data = json.loads(message["text"])
            event_type = data.get("type")

            if event_type == ClientEvent.START_UTTERANCE:
                session.start_utterance(data.get("mime_type"))
            elif event_type == ClientEvent.END_UTTERANCE:
                await workflow.process_audio_utterance(session, Trace())
            elif event_type == ClientEvent.TEXT_MESSAGE:
                text = str(data.get("text", "")).strip()
                if text:
                    await workflow.process_text_message(session, text, Trace())
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await publisher.emit(session, ServerEvent.ERROR, message=str(exc))
