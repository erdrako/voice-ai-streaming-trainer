from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application configuration.

    Production-oriented improvement:
    Instead of reading environment variables manually with `os.getenv`, this
    class validates settings at startup. That is closer to how enterprise apps
    treat configuration in .NET with strongly typed Options classes.

    Provider selection:
    The `*_provider` fields make implementations interchangeable at runtime.
    For example, switching from Piper to another TTS adapter should be a config
    plus composition-root change, not a workflow rewrite.

    Expansion point:
    - Add provider-specific fields here when creating new adapters.
    - Add environment-specific `.env` files such as `.env.local`, `.env.docker`,
      or `.env.test` if the project grows.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["local", "docker", "test", "production"] = "local"
    log_level: str = "INFO"

    stt_provider: Literal["faster_whisper_http", "template"] = "faster_whisper_http"
    llm_provider: Literal["ollama", "template"] = "ollama"
    tts_provider: Literal["piper_http", "template"] = "piper_http"
    event_bus_provider: Literal["redis", "none", "template"] = "redis"
    event_store_provider: Literal["sqlite", "template"] = "sqlite"

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"
    stt_base_url: str = "http://stt:9001"
    tts_base_url: str = "http://tts:9002"
    redis_url: str | None = "redis://redis:6379/0"
    database_path: str = "data/training.db"

    request_timeout_seconds: float = Field(default=180, gt=0)
    stt_timeout_seconds: float = Field(default=180, gt=0)
    llm_timeout_seconds: float = Field(default=180, gt=0)
    tts_timeout_seconds: float = Field(default=180, gt=0)
    readiness_timeout_seconds: float = Field(default=3, gt=0)

    provider_retry_attempts: int = Field(default=2, ge=1)
    provider_retry_backoff_seconds: float = Field(default=0.25, ge=0)

    partial_transcription_min_bytes: int = Field(default=120000, ge=0)
    partial_transcription_every_chunks: int = Field(default=4, ge=1)


@lru_cache
def get_settings() -> Settings:
    """Return cached validated settings for the current process."""

    return Settings()
