import httpx

from app.application.contracts.event_publisher import EventPublisher
from app.application.use_cases.voice_workflow import VoiceWorkflowUseCase
from app.config import Settings, get_settings
from app.domain.services.audio_format_service import AudioFormatService
from app.domain.services.segmentation_service import SegmentationService
from app.infrastructure.messaging.redis_event_bus import RedisEventBus
from app.infrastructure.persistence.sqlite_event_store import SqliteEventStore
from app.infrastructure.providers.llm.ollama_llm_provider import OllamaLanguageModelProvider
from app.infrastructure.providers.stt.http_stt_provider import HttpSpeechToTextProvider
from app.infrastructure.providers.tts.http_tts_provider import HttpTextToSpeechProvider


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

        self.event_store = SqliteEventStore(self.settings.database_path)
        self.event_bus = RedisEventBus(self.settings.redis_url)

        self.stt_provider = HttpSpeechToTextProvider(self.settings, self.http_client)
        self.llm_provider = OllamaLanguageModelProvider(self.settings, self.http_client)
        self.tts_provider = HttpTextToSpeechProvider(self.settings, self.http_client)

        self.audio_format_service = AudioFormatService()
        self.segmentation_service = SegmentationService()

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
