# Operacion local

## Levantar la app

```powershell
docker compose up -d --build
```

## Descargar modelo Ollama

```powershell
docker compose exec ollama ollama pull llama3.2:3b
```

## Verificar servicios

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:9001/health
Invoke-RestMethod http://127.0.0.1:9002/health
Invoke-RestMethod http://127.0.0.1:8000/metrics/recent
```

## Abrir la UI

```text
http://127.0.0.1:8000
```

## Checklist end-to-end

1. Abrir la UI.
2. Confirmar que el estado diga `Conectado`.
3. Enviar una pregunta por texto.
4. Ver tokens de respuesta en streaming.
5. Escuchar audio TTS por segmentos.
6. Grabar una frase corta.
7. Esperar el corte automatico por silencio o detener manualmente.
8. Ver parciales STT si la grabacion tuvo suficientes chunks.
9. Ver la transcripcion final.
10. Ver la respuesta del LLM.
11. Escuchar el audio generado.
12. Consultar `/metrics/recent`.

## Cambiar providers

El cambio de implementaciones se hace en:

```text
app/composition/container.py
```

Ejemplo conceptual:

```python
self.tts_provider = HttpTextToSpeechProvider(...)
```

Para agregar otro TTS:

1. Copiar `app/infrastructure/providers/tts/template_tts_provider.py`.
2. Implementar `synthesize_speech`.
3. Agregar configuracion en `app/config.py` si hace falta.
4. Registrar la nueva clase en `AppContainer`.
5. Correr tests.

## Problemas comunes

### Ollama no responde

Verificar contenedor:

```powershell
docker compose ps
```

Verificar modelos:

```powershell
docker compose exec ollama ollama list
```

### STT tarda mucho la primera vez

La primera transcripcion puede descargar el modelo de Whisper. El volumen `hf-cache` conserva ese cache.

### La transcripcion confunde palabras tecnicas

El modelo default `base` prioriza velocidad. Para mejor calidad:

```text
WHISPER_MODEL=small
```

### TTS tarda

La app sintetiza por segmentos. Si sigue tardando, suele ser por CPU local, por segmentos demasiado largos o por usar una maquina con pocos recursos.

### Redis no esta disponible fuera de Docker

El bus de eventos es best-effort. Si corres tests o API fuera de Docker sin Redis, la app sigue funcionando y descarta esos publishes.

### SQLite local

En Docker, la base vive en el volumen `app-data`. Fuera de Docker, el default es `data/training.db`.

## Comandos utiles

```powershell
docker compose logs api --tail 80
docker compose logs stt --tail 80
docker compose logs tts --tail 80
docker compose logs redis --tail 80
docker compose down
```
