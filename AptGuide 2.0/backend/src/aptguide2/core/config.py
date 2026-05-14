import os
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AptGuide 2.0 RAG layer configuration."""

    # Deployment
    environment: str = "local"  # local | staging | production
    service_name: str = "aptguide2"
    service_version: str = "0.1.0"
    cors_allow_origins: str = "http://localhost:5173"
    require_secure_defaults: bool = False

    # Observability
    log_level: str = "INFO"
    structured_logs_enabled: bool = True
    expose_trace_to_frontend: bool = True

    # Milvus
    milvus_uri: str = "http://localhost:19530"
    milvus_token: str = ""

    # Embedding (OpenAI-compatible)
    embedding_api_key: SecretStr = SecretStr("")
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # LLM (OpenAI-compatible)
    llm_api_key: SecretStr = SecretStr("")
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # Lease backend
    lease_base_url: str = "http://localhost:8081"
    lease_timeout_seconds: float = 5.0
    lease_internal_token: str = ""

    # KB
    kb_rules_dir: str = "knowledge/rules"

    # Interaction understanding
    intent_classifier_mode: str = "llm"  # llm | clarify_only
    intent_classifier_timeout_seconds: float = 3.0
    intent_classifier_min_confidence: float = 0.65

    # Harness
    pipeline_version: str = "harness_v1"
    harness_include_trace: bool = False

    # Standalone product
    app_mode: str = "standalone"
    frontend_origin: str = "http://localhost:5173"

    # Auth
    auth_mode: str = "dev"  # dev | lease_token
    dev_user_id: str = "dev-user-001"
    dev_user_name: str = "本地测试用户"
    lease_userinfo_path: str = "/app/info"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "aptguide2"
    session_ttl_seconds: int = 86400
    pending_action_ttl_seconds: int = 300

    # MySQL
    mysql_dsn: str = "mysql+asyncmy://root:change-me@localhost:3306/aptguide2"

    # Operator console
    operator_console_enabled: bool = True
    operator_dev_token: str = "operator-dev-token"

    # LangSmith observability
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_project: str = "aptguide2"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "aptguide2"

    # Langfuse observability
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://us.cloud.langfuse.com"

    model_config = {"env_prefix": "APTGUIDE_", "env_file": ".env"}

    @property
    def parsed_cors_origins(self) -> list[str]:
        values = [origin.strip() for origin in self.cors_allow_origins.split(",")]
        return [origin for origin in values if origin]


def _sync_langsmith_environment(settings: Settings) -> None:
    """Expose AptGuide-prefixed LangSmith settings for SDKs that read os.environ."""
    api_key = settings.langsmith_api_key or settings.langchain_api_key
    project = settings.langsmith_project or settings.langchain_project
    tracing = settings.langsmith_tracing or settings.langchain_tracing_v2
    values = {
        "LANGSMITH_TRACING": str(tracing).lower(),
        "LANGSMITH_ENDPOINT": settings.langsmith_endpoint,
        "LANGSMITH_API_KEY": api_key,
        "LANGSMITH_PROJECT": project,
        "LANGCHAIN_TRACING_V2": str(tracing).lower(),
        "LANGCHAIN_API_KEY": api_key,
        "LANGCHAIN_PROJECT": project,
    }
    for key, value in values.items():
        if value:
            os.environ[key] = value


def _sync_langfuse_environment(settings: Settings) -> None:
    """Expose Langfuse credentials as env vars for the langfuse SDK."""
    if not settings.langfuse_enabled:
        return
    values = {
        "LANGFUSE_PUBLIC_KEY": settings.langfuse_public_key,
        "LANGFUSE_SECRET_KEY": settings.langfuse_secret_key,
        "LANGFUSE_HOST": settings.langfuse_host,
    }
    for key, value in values.items():
        if value:
            os.environ[key] = value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _sync_langsmith_environment(settings)
    _sync_langfuse_environment(settings)
    return settings
