# Voice AI Streaming Trainer

Mini app local y dockerizada para practicar proyectos backend de IA aplicada a voz.

## Workflow end-to-end

```text
Browser
  -> WebSocket
  -> FastAPI API
  -> faster-whisper STT + parciales por buffer
  -> Ollama LLM streaming
  -> Piper TTS segmentado
  -> WAV al browser
```

El flujo es real y local:

1. El navegador graba audio desde el microfono.
2. La API recibe el audio por WebSocket.
3. La API llama al servicio `stt`, que transcribe con `faster-whisper`.
4. La API envia la transcripcion a `ollama`.
5. Ollama responde token a token y la API lo streamea al browser.
6. La API corta la respuesta en segmentos y sintetiza TTS por frase.
7. Piper genera WAVs parciales y el navegador los reproduce en cola.
8. La API registra eventos y metricas en SQLite y publica eventos en Redis.

## Stack

- `api`: FastAPI + WebSocket + HTTP clients async.
- `ollama`: LLM local. Default: `llama3.2:3b`.
- `stt`: FastAPI + `faster-whisper`. Default: modelo `base`.
- `tts`: FastAPI + Piper. Default: voz `es_ES-sharvard-medium`.
- `redis`: stream local de eventos para desacoplar observabilidad.
- `sqlite`: persistencia simple de sesiones, eventos y metricas.
- `docker-compose`: orquestacion local.

## Documentacion de entrenamiento

- [Arquitectura](docs/architecture.md)
- [Diagramas](docs/diagrams.md)
- [Operacion local](docs/operations.md)
- [Notas de entrevista](docs/interview-notes.md)

## Requisitos

- Docker Desktop.
- Espacio para imagenes y modelos.
- Primera ejecucion con internet para descargar imagenes, modelos de Whisper, Ollama y voz Piper.

## Ejecutar

```powershell
docker compose up -d --build
```

Descargar el modelo de Ollama:

```powershell
docker compose exec ollama ollama pull llama3.2:3b
```

Abrir:

```text
http://127.0.0.1:8000
```

## Modelos recomendados

Para maquinas chicas:

```text
OLLAMA_MODEL=llama3.2:3b
WHISPER_MODEL=base
```

Para mejor calidad si tenes mas RAM/CPU:

```text
OLLAMA_MODEL=qwen2.5:7b
WHISPER_MODEL=small
```

Con GPU NVIDIA, se puede evolucionar `stt` a:

```text
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
WHISPER_MODEL=large-v3-turbo
```

## Eventos WebSocket

Cliente a servidor:

```json
{ "type": "start_utterance", "mime_type": "audio/webm" }
```

Luego envia bytes binarios de audio.

```json
{ "type": "end_utterance" }
```

Tambien se puede enviar texto directo:

```json
{ "type": "text_message", "text": "Explicame esta arquitectura" }
```

Servidor a cliente:

```json
{ "type": "transcription.started" }
{ "type": "transcription.partial", "text": "..." }
{ "type": "transcription.completed", "text": "..." }
{ "type": "ai.response.started" }
{ "type": "ai.response.delta", "text": "..." }
{ "type": "ai.response.completed" }
{ "type": "tts.started", "segment": 1 }
{ "type": "tts.segment.completed", "mime_type": "audio/wav", "audio": "..." }
{ "type": "tts.completed", "segments": 2 }
{ "type": "metrics", "metrics": { "workflow_completed_ms": 1234.5 } }
```

## Como explicarlo en entrevista

Este MVP usa un flujo de voz por chunks: el browser envia audio mientras graba, un VAD simple corta por silencio, la API puede emitir parciales STT sobre el buffer acumulado, la respuesta del LLM se streamea token a token y el TTS se sintetiza por segmentos. Separar STT, LLM, TTS, Redis y SQLite permite explicar latencia, escalabilidad, observabilidad y cambios de proveedores sin tocar el contrato principal del backend.

## Tests

Los tests automaticos usan servicios fake para validar la orquestacion sin depender de modelos pesados.

```powershell
pytest
```

Para validar la app real con modelos locales, usa el checklist de [operacion local](docs/operations.md).
