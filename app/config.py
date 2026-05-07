from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    stt_base_url: str = os.getenv("STT_BASE_URL", "http://stt:9001")
    tts_base_url: str = os.getenv("TTS_BASE_URL", "http://tts:9002")
    redis_url: str | None = os.getenv("REDIS_URL", "redis://redis:6379/0")
    database_path: str = os.getenv("DATABASE_PATH", "data/training.db")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "180"))
    partial_transcription_min_bytes: int = int(os.getenv("PARTIAL_TRANSCRIPTION_MIN_BYTES", "120000"))
    partial_transcription_every_chunks: int = int(os.getenv("PARTIAL_TRANSCRIPTION_EVERY_CHUNKS", "4"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
