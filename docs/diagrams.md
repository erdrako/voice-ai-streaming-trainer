# Diagramas

## Arquitectura de servicios

```mermaid
flowchart LR
    Browser["Browser<br/>microfono + UI + VAD"] -->|WebSocket JSON + audio chunks| API["FastAPI API<br/>orquestador async"]
    API -->|POST /transcribe| STT["STT service<br/>faster-whisper"]
    API -->|POST /api/chat stream| Ollama["Ollama<br/>llama3.2:3b"]
    API -->|POST /synthesize| TTS["TTS service<br/>Piper"]
    API -->|XADD voice_ai_events| Redis["Redis<br/>event stream"]
    API -->|sessions/events/metrics| SQLite["SQLite<br/>training.db"]
    TTS -->|audio/wav| API
    Ollama -->|tokens| API
    STT -->|texto| API
    API -->|eventos + audio segments base64| Browser
```

## Secuencia end-to-end de voz

```mermaid
sequenceDiagram
    participant U as Usuario
    participant B as Browser
    participant A as FastAPI API
    participant S as STT faster-whisper
    participant O as Ollama
    participant T as Piper TTS

    U->>B: Presiona grabar
    B->>B: Captura audio con MediaRecorder
    B->>A: start_utterance
    loop Cada 750 ms
        B->>A: audio chunk
        A-->>B: transcription.partial opcional
    end
    B->>B: VAD detecta silencio
    B->>A: end_utterance
    A->>B: transcription.started
    A->>S: POST /transcribe
    S-->>A: texto transcripto
    A->>B: transcription.completed
    A->>O: POST /api/chat stream
    O-->>A: token
    A-->>B: ai.response.delta
    A->>A: Detecta frase completa
    A->>T: POST /synthesize segmento
    T-->>A: audio/wav segmento
    A-->>B: tts.segment.completed
    O-->>A: token
    A-->>B: ai.response.delta
    A->>B: ai.response.completed
    A-->>B: tts.completed
    A-->>B: metrics
    B->>U: Reproduce audio
```

## Flujo de decision en la API

```mermaid
flowchart TD
    Start["WebSocket message"] --> Type{"Tipo de mensaje"}
    Type -->|bytes| Append["Agregar bytes al buffer de audio"]
    Append --> Partial{"Corresponde parcial?"}
    Partial -->|si| PartialStt["Transcribir buffer acumulado"]
    PartialStt --> PartialEvent["Enviar transcription.partial"]
    Partial -->|no| Wait["Esperar siguiente mensaje"]
    PartialEvent --> Wait

    Type -->|start_utterance| Reset["Limpiar buffer y guardar mime_type"]
    Type -->|end_utterance| HasAudio{"Hay audio?"}
    Type -->|text_message| HasText{"Hay texto?"}

    HasAudio -->|no| AudioError["Enviar error"]
    HasAudio -->|si| Temp["Guardar audio temporal"]
    Temp --> Transcribe["Llamar STT"]
    Transcribe --> UserText["Agregar texto del usuario al historial"]

    HasText -->|no| Ignore["Ignorar"]
    HasText -->|si| UserText

    UserText --> LLM["Llamar Ollama en streaming"]
    LLM --> Delta["Enviar ai.response.delta"]
    Delta --> Segment{"Hay frase completa?"}
    Segment -->|si| SegmentTts["Sintetizar segmento TTS"]
    SegmentTts --> SegmentAudio["Enviar tts.segment.completed"]
    Segment -->|no| More{"Quedan tokens?"}
    SegmentAudio --> More
    More -->|si| Delta
    More -->|no| Store["Guardar respuesta completa"]
    Store --> Final["Enviar tts.completed y metrics"]
```

## Eventos WebSocket

```mermaid
flowchart LR
    subgraph Client["Cliente -> Servidor"]
        C1["start_utterance"]
        C2["audio bytes"]
        C3["end_utterance"]
        C4["text_message"]
    end

    subgraph Server["Servidor -> Cliente"]
        S1["session.ready"]
        S2["transcription.started"]
        S3["transcription.partial"]
        S4["transcription.completed"]
        S5["ai.response.started"]
        S6["ai.response.delta"]
        S7["ai.response.completed"]
        S8["tts.started"]
        S9["tts.segment.completed"]
        S10["tts.completed"]
        S11["metrics"]
        S12["error"]
    end
```

## Observabilidad y persistencia

```mermaid
flowchart TD
    API["FastAPI send_event"] --> Client["WebSocket client"]
    API --> Store["SQLite EventStore"]
    API --> Bus["Redis Stream voice_ai_events"]
    Store --> Recent["GET /metrics/recent"]
    Bus --> Future["Futuros workers / dashboard / alertas"]
```
