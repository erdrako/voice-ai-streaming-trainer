# Notas de entrevista

## Pitch corto

Este proyecto es un MVP local de IA aplicada a voz. Usa FastAPI con WebSocket para mantener una sesion interactiva, VAD simple en browser, faster-whisper para STT, Ollama para LLM local, Piper para TTS por segmentos, Redis para eventos internos y SQLite para trazas/metricas. Esta dockerizado con servicios separados para poder explicar escalabilidad, latencia e integracion entre componentes.

## Como describir el flujo

El cliente graba audio y lo envia por chunks al backend por WebSocket. Un VAD simple detecta silencio y cierra la utterance. La API no hace inferencia directamente: orquesta servicios especializados. Durante la grabacion puede emitir parciales STT sobre el buffer acumulado. Al final manda el audio al servicio STT, usa la transcripcion como mensaje del usuario, llama a Ollama con streaming y reenvia tokens al navegador. A medida que detecta frases completas, llama a TTS por segmento y devuelve WAVs parciales al cliente.

## Decisiones defendibles

- Use WebSocket porque necesito una sesion bidireccional.
- Separe STT, LLM y TTS para poder cambiar modelos y escalar etapas por separado.
- Use Docker Compose para reproducibilidad local.
- Agregue Redis como stream de eventos para desacoplar observabilidad.
- Agregue SQLite para poder auditar sesiones y metricas sin una base pesada.
- Sintetizo TTS por frases para mejorar latencia percibida.
- Use tests con fakes porque los modelos reales son lentos y no deberian ser dependencia de los tests unitarios.
- El STT parcial es una aproximacion por buffer acumulado, no streaming STT nativo.

## Limitaciones conscientes

- No hay transcripcion incremental nativa del motor.
- No hay autenticacion ni control de sesiones.
- No hay dashboard visual de metricas.
- Redis esta usado como stream local, no como sistema distribuido completo.

## Como lo evolucionaria

1. Reemplazaria el STT parcial por un motor con streaming real.
2. Agregaria un dashboard para ver trazas por sesion.
3. Moveria eventos criticos a workers dedicados.
4. Agregaria autenticacion y limites por sesion.
5. Separaria despliegue por recursos reales: CPU para API, GPU para STT/LLM si aplica.
6. Agregaria pruebas de carga y mediciones de latencia p95/p99.
