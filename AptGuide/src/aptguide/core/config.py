from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置。"""

    # LLM
    llm_api_key: SecretStr
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"

    # Embedding
    embedding_api_key: SecretStr
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v3"

    # Milvus
    milvus_uri: str = "http://localhost:19530"
    milvus_token: str = ""

    # Redis (阶段 3 启用)
    redis_url: str = "redis://localhost:6379/1"

    # 应用
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
