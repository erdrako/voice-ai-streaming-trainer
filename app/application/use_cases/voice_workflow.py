from pathlib import Path
from tempfile import NamedTemporaryFile
import base64

from app.application.contracts.event_publisher import EventPublisher
from app.application.contracts.language_model import LanguageModelProvider
from app.application.contracts.speech_to_text import SpeechToTextProvider
from app.application.contracts.text_to_speech import TextToSpeechProvider
from app.application.dto.voice_events import ServerEvent
from app.config import Settings
from app.domain.entities.voice_session import VoiceSession
from app.domain.services.audio_format_service import AudioFormatService
from app.domain.services.segmentation_service import SegmentationService
from app.infrastructure.telemetry.trace import Trace


class VoiceWorkflowUseCase:
    """
    Application-layer use case for the voice AI workflow.

    This is the heart of the Clean Architecture refactor. It coordinates the
    user workflow but delegates implementation details to injected contracts:

    - STT is delegated to SpeechToTextProvider.
    - LLM streaming is delegated to LanguageModelProvider.
    - TTS is delegated to TextToSpeechProvider.
    - Event output is delegated to EventPublisher.
    - Audio suffix and sentence segmentation are delegated to domain services.

    Dependency Injection:
    The constructor receives every dependency. This mirrors the .NET pattern of
    injecting interfaces into Application.Main classes. The class does not call
    `HttpTextToSpeechProvider()` or `RedisEventBus()` itself, which keeps it
    testable and replaceable.

    Expansion point:
    To replace a provider, add a new infrastructure implementation and register
    it in `composition/container.py`. This use case should not change unless
    the workflow itself changes.
    """

    def __init__(
        self,
        settings: Settings,
        stt_provider: SpeechToTextProvider,
        llm_provider: LanguageModelProvider,
        tts_provider: TextToSpeechProvider,
        event_publisher: EventPublisher,
        audio_format_service: AudioFormatService,
        segmentation_service: SegmentationService,
    ):
        """
        Variable guide:
        - `settings`: workflow thresholds and provider URLs/config.
        - `stt_provider`: interchangeable speech-to-text dependency.
        - `llm_provider`: interchangeable language model dependency.
        - `tts_provider`: interchangeable text-to-speech dependency.
        - `event_publisher`: output port used for WebSocket/client events.
        - `audio_format_service`: domain service for file suffix rules.
        - `segmentation_service`: domain service for TTS-ready text chunks.
        """

        self.settings = settings
        self.stt_provider = stt_provider
        self.llm_provider = llm_provider
        self.tts_provider = tts_provider
        self.event_publisher = event_publisher
        self.audio_format_service = audio_format_service
        self.segmentation_service = segmentation_service

    async def handle_audio_chunk(self, session: VoiceSession, chunk: bytes) -> None:
        """
        Add an audio chunk and optionally emit a partial transcription.

        Responsibility delegation:
        - The session entity mutates its own audio state.
        - The use case decides whether enough audio exists for partial STT.
        - The STT provider performs the actual transcription.
        """

        session.append_audio(chunk)
        await self._maybe_send_partial_transcription(session)

    async def process_audio_utterance(self, session: VoiceSession, trace: Trace) -> None:
        """
        Process a completed user utterance: STT -> LLM -> segmented TTS.

        This method is transport-agnostic. It does not know the utterance came
        from a WebSocket; it only sees a VoiceSession and emits events through
        the injected EventPublisher.
        """

        if not session.audio_buffer:
            await self.event_publisher.emit(
                session,
                ServerEvent.ERROR,
                message="No llego audio para transcribir.",
            )
            return

        temp_path = self._write_temp_audio(session)
        try:
            await self.event_publisher.emit(session, ServerEvent.TRANSCRIPTION_STARTED)
            text = await self.stt_provider.transcribe_audio(temp_path, session.mime_type)
            trace.mark("transcription_completed_ms")
            await self.event_publisher.emit(
                session,
                ServerEvent.TRANSCRIPTION_COMPLETED,
                text=text,
            )
            await self.process_text_message(session, text, trace)
        finally:
            temp_path.unlink(missing_ok=True)

    async def process_text_message(self, session: VoiceSession, text: str, trace: Trace) -> None:
        """
        Process a text turn: add user message, stream LLM, synthesize TTS.

        The same use case powers both text input and voice input after STT. This
        is a practical example of reusing application behavior behind multiple
        presentation paths.
        """

        session.add_user_text(text)
        await self.event_publisher.emit(session, ServerEvent.AI_RESPONSE_STARTED)

        full_response = ""
        segment_buffer = ""
        segment_index = 0

        async for delta in self.llm_provider.stream_response(session.conversation):
            full_response += delta
            segment_buffer += delta
            if "llm_first_token_ms" not in trace.marks:
                trace.mark("llm_first_token_ms")

            await self.event_publisher.emit(session, ServerEvent.AI_RESPONSE_DELTA, text=delta)

            ready_segments, segment_buffer = self.segmentation_service.extract_ready_segments(
                segment_buffer
            )
            for segment in ready_segments:
                if not self.segmentation_service.has_speakable_text(segment):
                    continue
                segment_index += 1
                await self._synthesize_segment(session, segment, segment_index)

        session.add_assistant_text(full_response)
        trace.mark("llm_completed_ms")
        await self.event_publisher.emit(session, ServerEvent.AI_RESPONSE_COMPLETED)

        remaining_segment = segment_buffer.strip()
        if self.segmentation_service.has_speakable_text(remaining_segment):
            segment_index += 1
            await self._synthesize_segment(session, remaining_segment, segment_index)

        trace.mark("workflow_completed_ms")
        await self.event_publisher.emit(session, ServerEvent.TTS_COMPLETED, segments=segment_index)
        await self.event_publisher.emit(session, ServerEvent.METRICS, metrics=trace.snapshot())

    async def _synthesize_segment(
        self,
        session: VoiceSession,
        text: str,
        segment_index: int,
    ) -> None:
        """
        Synthesize one TTS segment and emit it as base64 for the browser.

        Expansion point:
        If the UI later supports binary WebSocket frames for audio, replace this
        output format in a presentation-specific publisher instead of changing
        the TTS provider. The provider should keep returning raw audio bytes.
        """

        await self.event_publisher.emit(session, ServerEvent.TTS_STARTED, segment=segment_index)
        speech = await self.tts_provider.synthesize_speech(text)
        audio = base64.b64encode(speech).decode("ascii")
        await self.event_publisher.emit(
            session,
            ServerEvent.TTS_SEGMENT_COMPLETED,
            segment=segment_index,
            text=text,
            audio=audio,
            mime_type="audio/wav",
        )

    async def _maybe_send_partial_transcription(self, session: VoiceSession) -> None:
        """
        Emit partial STT when enough accumulated audio is available.

        This is not native streaming STT. It is a training-friendly approximation
        that re-transcribes the accumulated buffer every few chunks.

        Expansion point:
        Replace this with a streaming STT provider that supports partial results
        directly. The provider contract may then grow a streaming method, or a
        separate `StreamingSpeechToTextProvider` contract can be introduced.
        """

        enough_audio = len(session.audio_buffer) >= self.settings.partial_transcription_min_bytes
        enough_chunks = (
            session.audio_chunks_received - session.last_partial_chunk
            >= self.settings.partial_transcription_every_chunks
        )
        if not enough_audio or not enough_chunks:
            return

        session.last_partial_chunk = session.audio_chunks_received
        temp_path = self._write_temp_audio(session)
        try:
            text = await self.stt_provider.transcribe_audio(temp_path, session.mime_type)
            if text:
                await self.event_publisher.emit(
                    session,
                    ServerEvent.TRANSCRIPTION_PARTIAL,
                    text=text,
                )
        finally:
            temp_path.unlink(missing_ok=True)

    def _write_temp_audio(self, session: VoiceSession) -> Path:
        """
        Store current audio buffer in a temp file for providers that expect files.

        Expansion point:
        If future STT providers accept raw bytes or streams, add a provider
        contract that supports that shape. Keep this temp-file compatibility
        isolated in the use case or in a dedicated audio adapter.
        """

        suffix = self.audio_format_service.suffix_for_mime_type(session.mime_type)
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_audio.write(session.audio_buffer)
            return Path(temp_audio.name)
