# Notas de entrevista

## Pitch corto

Este proyecto es un MVP local de IA aplicada a voz con Clean Architecture / Hexagonal Architecture aplicada de forma didactica. Usa FastAPI con WebSocket para mantener una sesion interactiva, VAD simple en browser, faster-whisper para STT, Ollama para LLM local, Piper para TTS por segmentos, Redis para eventos internos y SQLite para trazas/metricas.

La app esta organizada en presentation, application, domain, infrastructure y composition root para practicar patrones de mercado: Dependency Injection, Dependency Inversion, contratos, adapters intercambiables y responsabilidad delegada.

## Como describir el flujo

El cliente graba audio y lo envia por chunks al backend por WebSocket. Un VAD simple detecta silencio y cierra la utterance. La presentation layer no hace inferencia directamente: parsea transporte y delega a `VoiceWorkflowUseCase`. El use case coordina STT, LLM y TTS usando contratos inyectados. A medida que detecta frases completas, llama a TTS por segmento y devuelve WAVs parciales al cliente mediante un `EventPublisher`.

## Decisiones defendibles

- Use WebSocket porque necesito una sesion bidireccional.
- Separe STT, LLM y TTS para poder cambiar modelos y escalar etapas por separado.
- Use Docker Compose para reproducibilidad local.
- Separe presentation/application/domain/infrastructure para que el codigo crezca con menor acoplamiento.
- Use constructor injection en los use cases.
- Use contratos `Protocol` para que la application layer no dependa de proveedores concretos.
- Agregue Redis como stream de eventos para desacoplar observabilidad.
- Agregue SQLite para poder auditar sesiones y metricas sin una base pesada.
- Sintetizo TTS por frases para mejorar latencia percibida.
- Use tests con fakes porque los modelos reales son lentos y no deberian ser dependencia de los tests unitarios.
- El STT parcial es una aproximacion por buffer acumulado, no streaming STT nativo.
- Agregue template providers para mostrar donde reemplazar STT, LLM, TTS, EventBus y EventStore.
- Agregue configuracion tipada con `pydantic-settings`.
- Agregue health checks separados para liveness/readiness.
- Agregue logging JSON estructurado.
- Agregue errores tipados, retry/backoff y fallback cuando falla TTS.

## Limitaciones conscientes

- No hay transcripcion incremental nativa del motor.
- No hay autenticacion ni control de sesiones.
- No hay dashboard visual de metricas.
- Redis esta usado como stream local, no como sistema distribuido completo.
- Los comentarios son mas largos que en produccion porque el repositorio es material de entrenamiento.

## Como lo evolucionaria

1. Reemplazaria el STT parcial por un motor con streaming real.
2. Agregaria un dashboard para ver trazas por sesion.
3. Moveria eventos criticos a workers dedicados.
4. Agregaria autenticacion y limites por sesion.
5. Separaria despliegue por recursos reales: CPU para API, GPU para STT/LLM si aplica.
6. Agregaria pruebas de carga y mediciones de latencia p95/p99.

## Frase util para entrevista

> Refactorice el MVP hacia una arquitectura por capas. FastAPI queda en presentation, la orquestacion vive en application use cases, las reglas puras viven en domain y los detalles de Ollama, STT, TTS, Redis y SQLite viven en infrastructure. El use case depende de contratos inyectados, asi que puedo reemplazar Piper por otro TTS o Redis por otro broker registrando otro adapter en el composition root.

## Frase sobre resiliencia

> Tambien agregue readiness checks, configuracion tipada, logging estructurado y manejo de fallos por proveedor. Por ejemplo, si falla TTS, el flujo no pierde la respuesta textual: emite un error con codigo estable y continua cerrando el workflow con metricas.
