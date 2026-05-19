import warnings
from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings

_DEFAULT_MYSQL_DSN = "mysql+asyncmy://root:change-me@localhost:3306/aptguide3"
_VALID_PERSISTENCE_MODES = {"memory", "mysql", "hybrid"}


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
    auth_mode: str = "dev"
    dev_user_id: str = "dev-user-001"
    dev_user_name: str = "本地测试用户"
    internal_token: SecretStr = SecretStr("")
    internal_token_required: bool = False
    cors_allow_origins: str = "http://localhost:5173"
    mysql_dsn: str = _DEFAULT_MYSQL_DSN
    persistence_mode: str = "memory"
    redis_key_prefix: str = "aptguide3"
    session_ttl_seconds: int = 86400
    pending_action_ttl_seconds: int = 300
    readiness_timeout_seconds: float = 2.0
    rag_room_top_k: int = 30
    rag_room_top_n: int = 5
    rag_kb_top_k: int = 10
    rag_preference_scorer_enabled: bool = True
    langsmith_tracing: bool = False
    langsmith_project: str = "aptguide3-local"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    understanding_diagnostics_enabled: bool = False

    model_config = {"env_prefix": "APTGUIDE3_", "env_file": ".env"}

    @field_validator("persistence_mode")
    @classmethod
    def validate_persistence_mode(cls, v: str) -> str:
        if v not in _VALID_PERSISTENCE_MODES:
            raise ValueError(
                f"persistence_mode must be one of {_VALID_PERSISTENCE_MODES}, got {v!r}"
            )
        return v

    def model_post_init(self, __context) -> None:
        if self.persistence_mode == "memory" and self.mysql_dsn != _DEFAULT_MYSQL_DSN:
            warnings.warn(
                "mysql_dsn is non-default but persistence_mode is 'memory'; "
                "MySQL will not be used. Set persistence_mode='mysql' or 'hybrid' to enable.",
                stacklevel=2,
            )

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
