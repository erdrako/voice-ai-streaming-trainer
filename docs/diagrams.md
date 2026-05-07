# Diagramas

## Capas

```mermaid
flowchart TD
    P["Presentation<br/>FastAPI + WebSocket"] --> A["Application<br/>Use cases + contracts"]
    A --> D["Domain<br/>Entities + domain services"]
    A --> C["Contracts<br/>STT / LLM / TTS / Store / Bus"]
    I["Infrastructure<br/>Concrete adapters"] --> C
    Comp["Composition Root<br/>container.py"] --> P
    Comp --> A
    Comp --> I
```

## Dependency Injection

```mermaid
flowchart LR
    Container["AppContainer"] --> STT["HttpSpeechToTextProvider"]
    Container --> LLM["OllamaLanguageModelProvider"]
    Container --> TTS["HttpTextToSpeechProvider"]
    Container --> Store["SqliteEventStore"]
    Container --> Bus["RedisEventBus"]
    Container --> UseCase["VoiceWorkflowUseCase"]
    Publisher["WebSocketEventPublisher"] --> UseCase
    UseCase --> STTContract["SpeechToTextProvider contract"]
    UseCase --> LLMContract["LanguageModelProvider contract"]
    UseCase --> TTSContract["TextToSpeechProvider contract"]
```

## Arquitectura de servicios runtime

```mermaid
flowchart LR
    Browser["Browser<br/>microfono + UI + VAD"] -->|WebSocket JSON + audio chunks| API["FastAPI API"]
    API -->|use case contract| STT["STT service<br/>faster-whisper"]
    API -->|use case contract| Ollama["Ollama<br/>llama3.2:3b"]
    API -->|use case contract| TTS["TTS service<br/>Piper"]
    API -->|EventBus contract| Redis["Redis<br/>event stream"]
    API -->|EventStore contract| SQLite["SQLite<br/>training.db"]
    TTS -->|audio/wav| API
    Ollama -->|tokens| API
    STT -->|texto| API
    API -->|events + audio segments| Browser
```

## Secuencia end-to-end de voz

```mermaid
sequenceDiagram
    participant B as Browser
    participant W as WebSocket Handler
    participant U as VoiceWorkflowUseCase
    participant S as STT Provider
    participant L as LLM Provider
    participant T as TTS Provider
    participant P as WebSocketEventPublisher
    participant O as SQLite/Redis

    B->>W: start_utterance
    B->>W: audio chunk
    W->>U: handle_audio_chunk(session, chunk)
    U->>S: transcribe_audio optional partial
    U->>P: transcription.partial
    P->>B: transcription.partial
    P->>O: persist/publish sanitized event
    B->>W: end_utterance
    W->>U: process_audio_utterance(session, trace)
    U->>S: transcribe_audio
    U->>P: transcription.completed
    U->>L: stream_response
    L-->>U: delta
    U->>P: ai.response.delta
    U->>T: synthesize_speech(segment)
    U->>P: tts.segment.completed
    P->>B: event + audio
    U->>P: metrics
```

## Provider replacement path

```mermaid
flowchart TD
    Problem["Need a second TTS provider"] --> Template["Copy template_tts_provider.py"]
    Template --> Implement["Implement synthesize_speech"]
    Implement --> Settings["Add provider config to Settings if needed"]
    Settings --> Container["Register in AppContainer"]
    Container --> Done["Use case unchanged"]
```

## Observabilidad y persistencia

```mermaid
flowchart TD
    UseCase["VoiceWorkflowUseCase"] --> Publisher["EventPublisher contract"]
    Publisher --> WebSocket["Browser WebSocket"]
    Publisher --> Store["EventStore contract"]
    Publisher --> Bus["EventBus contract"]
    Store --> SQLite["SqliteEventStore"]
    Bus --> Redis["RedisEventBus"]
    SQLite --> Recent["GET /metrics/recent"]
```

## Health readiness

```mermaid
flowchart TD
    Ready["GET /health/ready"] --> Container["AppContainer.readiness"]
    Container --> STT["STT /health"]
    Container --> TTS["TTS /health"]
    Container --> Ollama["Ollama /api/tags"]
    Container --> Store["EventStore check"]
    Container --> Bus["EventBus check"]
    STT --> Status["ready / not_ready"]
    TTS --> Status
    Ollama --> Status
    Store --> Status
    Bus --> Status
```

## Provider selection

```mermaid
flowchart LR
    Env["Environment variables"] --> Settings["Typed Settings"]
    Settings --> Container["AppContainer"]
    Container --> STTProvider["Selected STT provider"]
    Container --> LLMProvider["Selected LLM provider"]
    Container --> TTSProvider["Selected TTS provider"]
    Container --> StoreProvider["Selected EventStore"]
    Container --> BusProvider["Selected EventBus"]
```

## Exposure providers

```mermaid
flowchart TD
    Browser["Browser publico"] --> Provider["Exposure provider"]
    Provider --> Quick["Cloudflare Quick Tunnel<br/>sin dominio, URL temporal"]
    Provider --> Named["Cloudflare Named Tunnel<br/>Terraform + dominio propio"]
    Provider --> GCP["GCP Local Relay Reference<br/>sin recursos aplicados"]
    Quick --> Local["Backend local en esta maquina"]
    Named --> Local
    GCP --> Local
    Local --> Compose["Docker Compose<br/>FastAPI + Ollama + STT + TTS"]
```

## Cloudflare Quick Tunnel runtime

```mermaid
sequenceDiagram
    participant U as Browser
    participant CF as Cloudflare Edge
    participant C as cloudflared local
    participant A as FastAPI local
    participant AI as Ollama/STT/TTS local

    U->>CF: HTTPS / WebSocket
    CF->>C: Tunnel connection
    C->>A: http://host.docker.internal:8000
    A->>AI: STT -> LLM -> TTS
    AI-->>A: texto/audio
    A-->>C: WebSocket events
    C-->>CF: Tunnel response
    CF-->>U: UI + audio + streaming events
```
