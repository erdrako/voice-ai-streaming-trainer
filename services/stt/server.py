from pathlib import Path
from tempfile import NamedTemporaryFile
import asyncio
import os

from fastapi import FastAPI, UploadFile, File

from faster_whisper import WhisperModel


app = FastAPI(title="Local STT - faster-whisper")

model_name = os.getenv("WHISPER_MODEL", "base")
device = os.getenv("WHISPER_DEVICE", "cpu")
compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
model = WhisperModel(model_name, device=device, compute_type=compute_type)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": model_name}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(await file.read())
        temp_path = Path(temp_audio.name)

    try:
        def run() -> str:
            segments, _ = model.transcribe(
                str(temp_path),
                language="es",
                vad_filter=True,
                beam_size=5,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()

        text = await asyncio.to_thread(run)
        return {"text": text}
    finally:
        temp_path.unlink(missing_ok=True)
