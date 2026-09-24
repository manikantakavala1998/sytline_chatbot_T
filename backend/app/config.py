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
    temperature: float = 0.1
    max_tokens: int = 500

    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dim: int = 768

    api_host: str = "0.0.0.0"
    api_port: int = 8001

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Docker Milvus standalone (+ etcd + MinIO + Attu for browsing the
    # data visually). Point this at a local file path instead (e.g.
    # "data/vector_store/milvus.db") to fall back to Milvus Lite with no
    # containers — pymilvus's MilvusClient supports both via one URI.
    milvus_uri: str = "http://localhost:19530"


try:
    settings = Settings()
except Exception as exc:
    raise RuntimeError(
        "App settings are missing or invalid. Copy .env.example to .env and "
        "fill in OPENAI_API_KEY before starting the server."
    ) from exc
