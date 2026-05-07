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
5. Escuchar audio TTS al final.
6. Grabar una frase corta.
7. Ver la transcripcion.
8. Ver la respuesta del LLM.
9. Escuchar el audio generado.

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

### TTS tarda al final

Este MVP sintetiza la respuesta completa. Una mejora real seria sintetizar por frases mientras el LLM sigue generando.

## Comandos utiles

```powershell
docker compose logs api --tail 80
docker compose logs stt --tail 80
docker compose logs tts --tail 80
docker compose down
```

