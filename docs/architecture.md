# Arquitectura

Esta app es un proyecto de entrenamiento para practicar un backend de IA aplicada a voz. El objetivo no es crear un producto final, sino tener un MVP funcional que permita explicar decisiones tecnicas parecidas a las de proyectos reales: baja latencia, streaming, integracion con modelos locales, Docker, observabilidad y separacion de responsabilidades.

## Problema

El flujo simula un asistente de voz local:

1. El usuario graba audio desde el navegador.
2. El navegador envia chunks por WebSocket y corta la utterance con VAD simple.
3. Un servicio STT convierte audio a texto.
4. Un LLM local genera respuesta en streaming.
5. La API corta la respuesta en segmentos listos para voz.
6. Un servicio TTS convierte cada segmento a audio.
7. El navegador reproduce los segmentos de audio en orden.
8. La API registra eventos, metricas y trazas de la sesion.

## Servicios

### `api`

Responsabilidad principal: orquestar la sesion.

- Expone el frontend estatico.
- Mantiene el WebSocket con el navegador.
- Recibe chunks de audio binario y eventos JSON.
- Emite transcripciones parciales sobre el buffer acumulado.
- Llama a STT, Ollama y TTS.
- Streamea tokens del LLM hacia el cliente.
- Sintetiza TTS por segmentos mientras llegan frases completas.
- Publica eventos tecnicos en Redis.
- Persiste eventos y metricas en SQLite.
- Mantiene un historial simple por sesion WebSocket.

### `stt`

Responsabilidad principal: speech-to-text local.

- Expone `POST /transcribe`.
- Recibe un archivo de audio.
- Usa `faster-whisper`.
- Devuelve texto transcripto.

### `ollama`

Responsabilidad principal: inferencia LLM local.

- Expone la API nativa de Ollama.
- Recibe mensajes estilo chat.
- Devuelve tokens en streaming.
- Modelo default: `llama3.2:3b`.

### `tts`

Responsabilidad principal: text-to-speech local.

- Expone `POST /synthesize`.
- Recibe texto.
- Usa Piper con una voz en espanol.
- Devuelve audio WAV.

### `redis`

Responsabilidad principal: event stream interno.

- Recibe eventos en el stream `voice_ai_events`.
- Sirve como ejemplo de desacople para observabilidad o workers futuros.
- Es best-effort: si Redis no esta disponible fuera de Docker, la API sigue funcionando.

### `sqlite`

Responsabilidad principal: persistencia de entrenamiento.

- Guarda sesiones.
- Guarda eventos emitidos al cliente.
- Guarda payloads de metricas.
- Permite inspeccionar que paso durante una sesion sin montar una base pesada.

## Decisiones tecnicas

### Por que separar STT, LLM y TTS

Separar servicios permite cambiar una tecnologia sin reescribir todo el backend. Tambien facilita medir latencia por etapa:

- tiempo de subida del audio
- tiempo de transcripcion
- tiempo hasta el primer token del LLM
- tiempo total de generacion
- tiempo de sintetizado de voz

En produccion, cada servicio podria escalarse diferente. STT y TTS suelen necesitar CPU/GPU de forma distinta al LLM.

### Por que WebSocket

WebSocket mantiene una conexion persistente y permite enviar eventos en ambos sentidos:

- cliente a servidor: inicio de utterance, chunks de audio, fin de utterance
- servidor a cliente: transcripcion parcial, transcripcion final, tokens parciales, audio segmentado, metricas y errores

El navegador envia chunks de audio durante la grabacion y corta automaticamente con un VAD simple basado en energia. La API puede emitir transcripciones parciales re-transcribiendo el buffer acumulado cada cierta cantidad de chunks. La respuesta del LLM se streamea token a token.

### Como se mide latencia

Cada workflow crea una traza local. La API marca:

- `transcription_completed_ms`
- `llm_first_token_ms`
- `llm_completed_ms`
- `workflow_completed_ms`

Esas metricas se envian al cliente como evento `metrics` y tambien quedan persistidas.

### TTS por segmentos

Mientras Ollama genera tokens, la API acumula texto hasta detectar una frase completa. Cuando aparece un segmento terminado, lo manda a Piper y envia al navegador `tts.segment.completed`. Esto reduce la espera percibida frente a sintetizar toda la respuesta al final.

## Que es real y que esta acotado

Real:

- audio desde navegador
- VAD simple en navegador
- chunks de audio durante la grabacion
- transcripcion parcial por buffer acumulado
- transcripcion local
- LLM local
- TTS local por segmentos
- Docker Compose
- WebSocket
- Redis para eventos internos
- SQLite para eventos y metricas

Acotado:

- la transcripcion parcial reusa el buffer acumulado; no es STT incremental nativo
- no hay autenticacion
- no hay dashboard de observabilidad
- Redis se usa como stream local, no como arquitectura distribuida completa

## Evolucion implementada

Se implementaron los pasos de evolucion propuestos:

1. VAD simple en browser para cortar utterances por silencio.
2. Envio de chunks de audio con `MediaRecorder.start(750)`.
3. Transcripcion parcial por buffer acumulado con `transcription.partial`.
4. Respuesta LLM por streaming token a token.
5. TTS por segmentos de frase.
6. Redis Stream `voice_ai_events` para eventos internos.
7. SQLite para sesiones, eventos y metricas.
8. Reservas de recursos por servicio en Docker Compose.

El punto 3 es una aproximacion del MVP: `faster-whisper` no se usa como streaming STT nativo, sino que se invoca sobre audio acumulado para obtener parciales.
