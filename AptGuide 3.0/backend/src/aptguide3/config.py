from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "local"
    service_name: str = "aptguide3"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = "qwen-turbo-latest"
    understanding_min_confidence: float = 0.65
    lease_base_url: str = "http://localhost:8081"
    lease_timeout_seconds: float = 5.0
    vector_uri: str = "http://localhost:19530"
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: SecretStr = SecretStr("")
    embedding_model: str = "text-embedding-3-small"
    redis_url: str = ""

    model_config = {"env_prefix": "APTGUIDE3_", "env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
