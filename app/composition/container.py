import asyncio

import httpx

from app.application.contracts.event_publisher import EventPublisher
from app.application.use_cases.voice_workflow import VoiceWorkflowUseCase
from app.config import Settings, get_settings
from app.domain.services.audio_format_service import AudioFormatService
from app.domain.services.segmentation_service import SegmentationService
from app.infrastructure.messaging.noop_event_bus import NoOpEventBus
from app.infrastructure.messaging.redis_event_bus import RedisEventBus
from app.infrastructure.messaging.template_event_bus import TemplateEventBus
from app.infrastructure.persistence.sqlite_event_store import SqliteEventStore
from app.infrastructure.persistence.template_event_store import TemplateEventStore
from app.infrastructure.providers.llm.ollama_llm_provider import OllamaLanguageModelProvider
from app.infrastructure.providers.llm.template_llm_provider import TemplateLanguageModelProvider
from app.infrastructure.providers.stt.http_stt_provider import HttpSpeechToTextProvider
from app.infrastructure.providers.stt.template_stt_provider import TemplateSpeechToTextProvider
from app.infrastructure.providers.tts.http_tts_provider import HttpTextToSpeechProvider
from app.infrastructure.providers.tts.template_tts_provider import TemplateTextToSpeechProvider


class AppContainer:
    """
    Composition root / Dependency Injection container.

    This file is the Python equivalent of a .NET `ConfigureServices` module.
    It is the one place where concrete infrastructure classes are selected and
    wired into application use cases.

    Why this matters:
    - Use cases do not instantiate concrete providers.
    - Tests can replace providers with fakes.
    - Future provider swaps happen here, not across the whole codebase.

    Expansion point:
    - Replace `HttpTextToSpeechProvider` with a new TTS implementation here.
    - Replace `RedisEventBus` with Kafka/RabbitMQ/NATS here.
    - Replace `SqliteEventStore` with PostgreSQL here.
    """

    def __init__(self, settings: Settings | None = None):
        """
        Variables:
        - `settings`: application configuration.
        - `http_client`: shared async HTTP client for provider adapters.
        - `event_store`: concrete persistence adapter.
        - `event_bus`: concrete messaging adapter.
        - `*_provider`: concrete STT/LLM/TTS adapters.
        - domain services: stateless reusable rule objects.
        """

        self.settings = settings or get_settings()
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        self.http_client = httpx.AsyncClient(timeout=timeout)

        self.event_store = self._create_event_store()
        self.event_bus = self._create_event_bus()

        self.stt_provider = self._create_stt_provider()
        self.llm_provider = self._create_llm_provider()
        self.tts_provider = self._create_tts_provider()

        self.audio_format_service = AudioFormatService()
        self.segmentation_service = SegmentationService()

    def _create_event_store(self):
        """
        Select EventStore implementation from configuration.

        Production-oriented improvement:
        Provider selection via config is how the templates become actionable.
        """

        if self.settings.event_store_provider == "sqlite":
            return SqliteEventStore(self.settings.database_path)
        if self.settings.event_store_provider == "template":
            return TemplateEventStore()
        raise ValueError(f"Unsupported EVENT_STORE_PROVIDER={self.settings.event_store_provider}")

    def _create_event_bus(self):
        """Select EventBus implementation from configuration."""

        if self.settings.event_bus_provider == "redis":
            return RedisEventBus(self.settings.redis_url)
        if self.settings.event_bus_provider == "none":
            return NoOpEventBus()
        if self.settings.event_bus_provider == "template":
            return TemplateEventBus()
        raise ValueError(f"Unsupported EVENT_BUS_PROVIDER={self.settings.event_bus_provider}")

    def _create_stt_provider(self):
        """Select STT implementation from configuration."""

        if self.settings.stt_provider == "faster_whisper_http":
            return HttpSpeechToTextProvider(self.settings, self.http_client)
        if self.settings.stt_provider == "template":
            return TemplateSpeechToTextProvider()
        raise ValueError(f"Unsupported STT_PROVIDER={self.settings.stt_provider}")

    def _create_llm_provider(self):
        """Select LLM implementation from configuration."""

        if self.settings.llm_provider == "ollama":
            return OllamaLanguageModelProvider(self.settings, self.http_client)
        if self.settings.llm_provider == "template":
            return TemplateLanguageModelProvider()
        raise ValueError(f"Unsupported LLM_PROVIDER={self.settings.llm_provider}")

    def _create_tts_provider(self):
        """Select TTS implementation from configuration."""

        if self.settings.tts_provider == "piper_http":
            return HttpTextToSpeechProvider(self.settings, self.http_client)
        if self.settings.tts_provider == "template":
            return TemplateTextToSpeechProvider()
        raise ValueError(f"Unsupported TTS_PROVIDER={self.settings.tts_provider}")

    async def readiness(self) -> dict:
        """
        Check external dependencies needed for the real workflow.

        Production-oriented improvement:
        `/health/live` says the process is up. `/health/ready` says the process
        can actually serve traffic because its providers are reachable.
        """

        checks = {
            "event_store": self._check_event_store(),
            "event_bus": await self._check_event_bus(),
            "stt": await self._check_http_health(self.settings.stt_base_url),
            "tts": await self._check_http_health(self.settings.tts_base_url),
            "ollama": await self._check_ollama(),
        }
        ready = all(check["ok"] for check in checks.values())
        return {"status": "ready" if ready else "not_ready", "checks": checks}

    def _check_event_store(self) -> dict:
        try:
            self.event_store.recent_events(1)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _check_event_bus(self) -> dict:
        if isinstance(self.event_bus, NoOpEventBus):
            return {"ok": True, "mode": "disabled"}
        try:
            client = getattr(self.event_bus, "client", None)
            if client is not None:
                await asyncio.wait_for(
                    client.ping(),
                    timeout=self.settings.readiness_timeout_seconds,
                )
            await self.event_bus.publish("readiness", "health.ready", {"ok": True})
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _check_http_health(self, base_url: str) -> dict:
        try:
            response = await self.http_client.get(
                f"{base_url}/health",
                timeout=self.settings.readiness_timeout_seconds,
            )
            response.raise_for_status()
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _check_ollama(self) -> dict:
        try:
            response = await self.http_client.get(
                f"{self.settings.ollama_base_url}/api/tags",
                timeout=self.settings.readiness_timeout_seconds,
            )
            response.raise_for_status()
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def create_voice_workflow(self, event_publisher: EventPublisher) -> VoiceWorkflowUseCase:
        """
        Factory method for a per-connection use case.

        The event publisher is per WebSocket connection, while providers and
        stores can be shared. This mirrors scoped dependencies in .NET.
        """

        return VoiceWorkflowUseCase(
            settings=self.settings,
            stt_provider=self.stt_provider,
            llm_provider=self.llm_provider,
            tts_provider=self.tts_provider,
            event_publisher=event_publisher,
            audio_format_service=self.audio_format_service,
            segmentation_service=self.segmentation_service,
        )

    async def close(self) -> None:
        """Release shared resources when FastAPI shuts down."""

        await self.event_bus.close()
        await self.http_client.aclose()
