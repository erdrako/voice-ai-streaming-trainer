from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    stt_base_url: str = os.getenv("STT_BASE_URL", "http://stt:9001")
    tts_base_url: str = os.getenv("TTS_BASE_URL", "http://tts:9002")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "180"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
