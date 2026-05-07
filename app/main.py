from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.composition.container import AppContainer
from app.infrastructure.logging.structured import configure_logging
from app.presentation.websocket.event_publisher import sanitize_payload
from app.presentation.websocket.voice_socket import handle_voice_session


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Composition root:
# A single container is created when the app module is imported. In .NET terms,
# this is similar to building the service provider in Program.cs.
container = AppContainer()
configure_logging(container.settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifecycle hook.

    Responsibility:
    - Keep startup/shutdown concerns in the presentation/bootstrap layer.
    - Delegate resource cleanup to the DI container, which owns shared clients.
    """

    yield
    await container.close()


app = FastAPI(title="Voice AI Streaming Trainer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Thin HTTP endpoint for Docker/local health checks.

    This route intentionally contains no business logic. It is part of the
    presentation layer.
    """

    return {"status": "ok"}


@app.get("/health/live")
async def live() -> dict[str, str]:
    """
    Liveness probe.

    Production-oriented improvement:
    This endpoint only confirms that the API process can answer. It does not
    check dependencies.
    """

    return {"status": "alive"}


@app.get("/health/ready")
async def ready() -> dict:
    """
    Readiness probe.

    Production-oriented improvement:
    This endpoint checks STT, TTS, Ollama, event store and event bus reachability
    so an orchestrator could decide whether to route traffic here.
    """

    return await container.readiness()


@app.get("/metrics/recent")
async def recent_metrics() -> list[dict]:
    """
    HTTP diagnostics endpoint.

    The route delegates to the injected EventStore implementation. If SQLite is
    replaced by PostgreSQL later, this route should remain unchanged.
    """

    return container.event_store.recent_events()


@app.get("/")
async def index() -> HTMLResponse:
    """Serve the training UI from the presentation/static layer."""

    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket entry point.

    The handler delegates transport details to `handle_voice_session`, which in
    turn delegates workflow behavior to application use cases.
    """

    await handle_voice_session(websocket, session_id, container)
