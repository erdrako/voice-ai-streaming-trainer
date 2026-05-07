# Notas de entrevista

## Pitch corto

Este proyecto es un MVP local de IA aplicada a voz. Usa FastAPI con WebSocket para mantener una sesion interactiva, faster-whisper para STT, Ollama para LLM local y Piper para TTS. Esta dockerizado con servicios separados para poder explicar escalabilidad, latencia e integracion entre componentes.

## Como describir el flujo

El cliente graba audio y lo envia al backend por WebSocket. La API no hace inferencia directamente: orquesta servicios especializados. Primero manda el audio al servicio STT, despues usa la transcripcion como mensaje del usuario, llama a Ollama con streaming y reenvia los tokens al navegador. Cuando termina la respuesta, llama a TTS y devuelve un WAV al cliente.

## Decisiones defendibles

- Use WebSocket porque necesito una sesion bidireccional.
- Separe STT, LLM y TTS para poder cambiar modelos y escalar etapas por separado.
- Use Docker Compose para reproducibilidad local.
- Use tests con fakes porque los modelos reales son lentos y no deberian ser dependencia de los tests unitarios.
- El MVP procesa audio por utterance, pero la respuesta del LLM si se streamea.

## Limitaciones conscientes

- No hay transcripcion incremental real.
- No hay VAD del lado cliente.
- No hay persistencia de conversaciones.
- No hay autenticacion ni control de sesiones.
- No hay metricas formales de latencia.
- El TTS se genera cuando termina toda la respuesta.

## Como lo evolucionaria

1. Mediria latencia por etapa.
2. Agregaria VAD y chunks parciales de audio.
3. Evaluaria STT incremental.
4. Haria TTS por segmentos.
5. Agregaria Redis o Kafka si necesito desacoplar eventos.
6. Persistiria sesiones y trazas.
7. Separaria despliegue por recursos: CPU para API, GPU para STT/LLM si aplica.

