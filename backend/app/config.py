"""
All app settings live here, loaded from the .env file.
If OPENAI_API_KEY is missing, this fails immediately on startup instead of
failing later in the middle of a chat request.
"""

import sys
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


BASE_DIR = get_base_dir()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str

    @field_validator("openai_api_key")
    @classmethod
    def openai_api_key_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("OPENAI_API_KEY is blank — paste your real key into .env")
        return value

    primary_llm: str = "gpt-4.1"
    orchestrator_model: str = "gpt-4.1-mini"
    orchestrator_llm_enabled: bool = True
    orchestrator_timeout_seconds: float = 12.0
    temperature: float = 0.1
    max_tokens: int = 500

    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dim: int = 768

    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Ports match this project's own docker-compose.yml (ptc-redis), not
    # the default Redis port — kept different on purpose so this project
    # never collides with some other Redis container on the same machine.
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0

    # Docker Milvus standalone (+ etcd + MinIO + Attu for browsing the
    # data visually) — ptc-milvus from this project's own docker-compose.yml,
    # on a non-default port for the same isolation reason as Redis above.
    # Point this at a local file path instead (e.g.
    # "data/vector_store/milvus.db") to fall back to Milvus Lite with no
    # containers — pymilvus's MilvusClient supports both via one URI.
    milvus_uri: str = "http://localhost:19531"


try:
    settings = Settings()
except Exception as exc:
    raise RuntimeError(
        "App settings are missing or invalid. Copy .env.example to .env and "
        "fill in OPENAI_API_KEY before starting the server."
    ) from exc
