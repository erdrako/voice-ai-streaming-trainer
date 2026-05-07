# Arquitectura

Esta app es un proyecto de entrenamiento para practicar un backend de IA aplicada a voz. El objetivo no es crear un producto final, sino tener un MVP funcional que permita explicar decisiones tecnicas parecidas a las de proyectos reales: baja latencia, streaming, integracion con modelos locales, Docker y separacion de responsabilidades.

## Problema

El flujo simula un asistente de voz local:

1. El usuario graba audio desde el navegador.
2. El backend recibe la grabacion por WebSocket.
3. Un servicio STT convierte audio a texto.
4. Un LLM local genera respuesta en streaming.
5. Un servicio TTS convierte la respuesta final a audio.
6. El navegador reproduce el audio generado.

## Servicios

### `api`

Responsabilidad principal: orquestar la sesion.

- Expone el frontend estatico.
- Mantiene el WebSocket con el navegador.
- Recibe audio binario y eventos JSON.
- Llama a STT, Ollama y TTS.
- Streamea tokens del LLM hacia el cliente.
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

- cliente a servidor: inicio de utterance, bytes de audio, fin de utterance
- servidor a cliente: transcripcion, tokens parciales, audio final, errores

Para este MVP, el audio se envia al final de la grabacion. La respuesta del LLM si se streamea token a token.

### Que es real y que esta acotado

Real:

- audio desde navegador
- transcripcion local
- LLM local
- TTS local
- Docker Compose
- WebSocket

Acotado:

- no hay STT incremental por chunks
- no hay VAD en el navegador
- no hay persistencia
- no hay autenticacion
- no hay observabilidad formal
- no hay cola distribuida

## Evolucion natural

Para acercarlo a una arquitectura de baja latencia real:

1. Agregar VAD para detectar cuando el usuario empieza y termina de hablar.
2. Enviar chunks de audio durante la grabacion.
3. Usar STT incremental o partial transcription.
4. Enviar la respuesta del LLM por segmentos semanticos.
5. Sintetizar TTS por frases, no al final de toda la respuesta.
6. Agregar Redis/Kafka para desacoplar eventos.
7. Medir latencia con trazas y metricas por etapa.
8. Desplegar servicios con recursos independientes.

