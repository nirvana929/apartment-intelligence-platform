from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    """AptGuide 2.0 RAG layer configuration."""

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

    # LangSmith observability
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "aptguide2"

    model_config = {"env_prefix": "APTGUIDE_", "env_file": ".env"}
