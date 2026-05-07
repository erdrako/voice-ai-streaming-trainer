from pathlib import Path
from tempfile import NamedTemporaryFile
import asyncio
import os
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel


app = FastAPI(title="Local TTS - Piper")


class SpeechRequest(BaseModel):
    text: str


@app.get("/health")
async def health() -> dict[str, str]:
    model_path = os.getenv("PIPER_MODEL", "/voices/es_ES-sharvard-medium.onnx")
    return {"status": "ok", "model": model_path}


@app.post("/synthesize")
async def synthesize(request: SpeechRequest) -> Response:
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    model_path = os.getenv("PIPER_MODEL", "/voices/es_ES-sharvard-medium.onnx")
    if not Path(model_path).exists():
        raise HTTPException(status_code=500, detail=f"Piper model not found: {model_path}")

    with NamedTemporaryFile(delete=False, suffix=".wav") as output:
        output_path = Path(output.name)

    try:
        def run() -> None:
            subprocess.run(
                ["piper", "--model", model_path, "--output_file", str(output_path)],
                input=text,
                text=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        await asyncio.to_thread(run)
        return Response(output_path.read_bytes(), media_type="audio/wav")
    finally:
        output_path.unlink(missing_ok=True)
