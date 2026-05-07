# Arquitectura

Esta app es un proyecto de entrenamiento para practicar un backend de IA aplicada a voz con una estructura intencionalmente enterprise. El objetivo no es minimizar archivos, sino familiarizarse con capas, contratos, Dependency Injection, responsabilidad delegada y puntos de extension intercambiables.

## Capas

```text
app/
  presentation/
  application/
  domain/
  infrastructure/
  composition/
```

### Presentation

Ubicacion:

```text
app/presentation/
app/main.py
static/
```

Responsabilidad:

- Exponer HTTP/WebSocket.
- Parsear eventos del browser.
- Enviar respuestas al cliente.
- Delegar el workflow a application use cases.

No deberia:

- Llamar directamente a Ollama/STT/TTS.
- Tener reglas de negocio.
- Conocer SQL, Redis o detalles de proveedores.

Archivos clave:

- `app/main.py`: bootstrap FastAPI, health, metrics y WebSocket entrypoint.
- `app/presentation/websocket/voice_socket.py`: handler de WebSocket.
- `app/presentation/websocket/event_publisher.py`: adapter de salida para WebSocket.

### Application

Ubicacion:

```text
app/application/
```

Responsabilidad:

- Orquestar casos de uso.
- Definir contratos que necesita la app.
- Coordinar STT -> LLM -> TTS sin conocer implementaciones concretas.

Archivos clave:

- `app/application/use_cases/voice_workflow.py`
- `app/application/contracts/speech_to_text.py`
- `app/application/contracts/language_model.py`
- `app/application/contracts/text_to_speech.py`
- `app/application/contracts/event_store.py`
- `app/application/contracts/event_bus.py`
- `app/application/contracts/event_publisher.py`

### Domain

Ubicacion:

```text
app/domain/
```

Responsabilidad:

- Entidades y reglas puras.
- Sin FastAPI, HTTPX, Redis, SQLite ni Docker.

Archivos clave:

- `app/domain/entities/voice_session.py`
- `app/domain/services/audio_format_service.py`
- `app/domain/services/segmentation_service.py`

### Infrastructure

Ubicacion:

```text
app/infrastructure/
```

Responsabilidad:

- Implementar contratos definidos por application.
- Encapsular detalles tecnicos de proveedores externos/locales.

Implementaciones reales:

- STT: `app/infrastructure/providers/stt/http_stt_provider.py`
- LLM: `app/infrastructure/providers/llm/ollama_llm_provider.py`
- TTS: `app/infrastructure/providers/tts/http_tts_provider.py`
- Redis: `app/infrastructure/messaging/redis_event_bus.py`
- SQLite: `app/infrastructure/persistence/sqlite_event_store.py`
- Telemetry: `app/infrastructure/telemetry/trace.py`

Templates de extension:

- `template_stt_provider.py`
- `template_llm_provider.py`
- `template_tts_provider.py`
- `template_event_bus.py`
- `template_event_store.py`

### Composition

Ubicacion:

```text
app/composition/container.py
```

Responsabilidad:

- Crear dependencias concretas.
- Inyectarlas en los use cases.
- Actuar como equivalente Python de `ConfigureServices.cs` o `Program.cs` en .NET.

## Mapeo con .NET

```text
Pacagroup.Ecommerce.Services.WebApi
  -> app/presentation + app/main.py

Pacagroup.Ecommerce.Application.Interface
  -> app/application/contracts

Pacagroup.Ecommerce.Application.Main
  -> app/application/use_cases

Pacagroup.Ecommerce.Domain.Entity
  -> app/domain/entities

Pacagroup.Ecommerce.Domain.Core
  -> app/domain/services

Pacagroup.Ecommerce.Infrastructure.Repository/Data
  -> app/infrastructure/persistence

Pacagroup.Ecommerce.Transversal.*
  -> app/infrastructure/telemetry + app/config.py

ConfigureServices.cs
  -> app/composition/container.py
```

## Dependency Injection

El use case no instancia proveedores concretos:

```python
class VoiceWorkflowUseCase:
    def __init__(self, stt_provider, llm_provider, tts_provider, event_publisher, ...):
        ...
```

El container decide que implementacion usar:

```python
self.stt_provider = HttpSpeechToTextProvider(...)
self.llm_provider = OllamaLanguageModelProvider(...)
self.tts_provider = HttpTextToSpeechProvider(...)
```

Si Piper falla o se necesita otro TTS:

1. Crear una nueva clase en `app/infrastructure/providers/tts/`.
2. Usar `template_tts_provider.py` como guia.
3. Registrar la nueva clase en `app/composition/container.py`.
4. No tocar `VoiceWorkflowUseCase`.

## Configuracion y seleccion de providers

La configuracion vive en:

```text
app/config.py
```

Usa `pydantic-settings`, por lo que las variables se validan al iniciar. Esto
es similar a usar Options tipadas en .NET.

Variables importantes:

```text
STT_PROVIDER=faster_whisper_http
LLM_PROVIDER=ollama
TTS_PROVIDER=piper_http
EVENT_BUS_PROVIDER=redis
EVENT_STORE_PROVIDER=sqlite
```

El selection logic esta centralizado en:

```text
app/composition/container.py
```

Esto permite cambiar implementaciones sin tocar el use case.

## Health checks

Endpoints:

```text
/health/live
/health/ready
```

`/health/live` valida que el proceso responde. `/health/ready` valida
dependencias necesarias para servir trafico real:

- STT `/health`
- TTS `/health`
- Ollama `/api/tags`
- EventStore
- EventBus

## Logging y resiliencia

Logging:

```text
app/infrastructure/logging/structured.py
```

El logger escribe JSON para que sea mas facil enviarlo a una plataforma de
observabilidad.

Retry/backoff:

```text
app/infrastructure/resilience/retry.py
```

Los providers HTTP usan una politica simple de retry. En produccion podria
reemplazarse por Tenacity, OpenTelemetry, circuit breakers o un gateway interno.

Errores:

```text
app/application/exceptions.py
```

Los providers traducen fallos tecnicos a errores con codigos estables como:

```text
STT_PROVIDER_UNAVAILABLE
LLM_PROVIDER_UNAVAILABLE
TTS_PROVIDER_UNAVAILABLE
```

El use case puede manejar cada caso sin filtrar detalles internos al cliente.

## Workflow actual

1. Browser envia `start_utterance`.
2. Browser envia audio chunks por WebSocket.
3. `voice_socket.py` delega chunks a `VoiceWorkflowUseCase.handle_audio_chunk`.
4. El use case puede emitir `transcription.partial`.
5. Browser envia `end_utterance`.
6. El use case llama STT por contrato.
7. El use case agrega el texto a `VoiceSession`.
8. El use case llama LLM por contrato y streamea deltas.
9. `SegmentationService` detecta frases listas para TTS.
10. El use case llama TTS por contrato.
11. `WebSocketEventPublisher` envia eventos al cliente.
12. El publisher persiste eventos en SQLite y publica en Redis.

## Puntos de extension

### Exposure / Deployment

La exposicion publica se trata como otro punto intercambiable, igual que STT,
LLM, TTS, persistence y messaging:

```text
infra/cloudflare/quick-tunnel
infra/terraform/cloudflare-named-tunnel
infra/terraform/gcp-local-relay-reference
```

Implementacion funcional sin dominio:

```text
cloudflare_quick_tunnel
```

Implementacion futura con dominio:

```text
cloudflare_named_tunnel
```

Referencia GCP sin recursos reales:

```text
gcp_local_relay_reference
```

La razon de esta separacion es la misma que en los providers de codigo: cambiar
la forma de exponer la app no deberia cambiar el workflow de voz ni los casos de
uso internos.

### STT

Contrato:

```text
app/application/contracts/speech_to_text.py
```

Implementacion actual:

```text
app/infrastructure/providers/stt/http_stt_provider.py
```

Template:

```text
app/infrastructure/providers/stt/template_stt_provider.py
```

### LLM

Contrato:

```text
app/application/contracts/language_model.py
```

Implementacion actual:

```text
app/infrastructure/providers/llm/ollama_llm_provider.py
```

Template:

```text
app/infrastructure/providers/llm/template_llm_provider.py
```

### TTS

Contrato:

```text
app/application/contracts/text_to_speech.py
```

Implementacion actual:

```text
app/infrastructure/providers/tts/http_tts_provider.py
```

Template:

```text
app/infrastructure/providers/tts/template_tts_provider.py
```

### Persistence

Contrato:

```text
app/application/contracts/event_store.py
```

Implementacion actual:

```text
app/infrastructure/persistence/sqlite_event_store.py
```

Template:

```text
app/infrastructure/persistence/template_event_store.py
```

### Messaging

Contrato:

```text
app/application/contracts/event_bus.py
```

Implementacion actual:

```text
app/infrastructure/messaging/redis_event_bus.py
```

Template:

```text
app/infrastructure/messaging/template_event_bus.py
```

## Sobre el nivel de comentarios

El proyecto tiene comentarios mas detallados que un repositorio productivo normal porque tambien funciona como material de entrenamiento. Los comentarios explican:

- responsabilidad de cada capa
- variables importantes
- donde se aplica Dependency Injection
- donde se delega responsabilidad
- donde se puede agregar una implementacion alternativa
