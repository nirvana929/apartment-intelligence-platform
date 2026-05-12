"""
应用配置模块 —— 用 pydantic-settings 管理所有配置。

【学习要点】
1. BaseSettings 是 pydantic-settings 提供的类，能自动从环境变量 / .env 文件读取配置
2. SecretStr 是 pydantic 的特殊类型，打印时自动显示为 **********，防止密钥泄露
3. model_config 告诉 pydantic 去哪里找 .env 文件
4. 字段名 llm_api_key 会自动映射到环境变量 LLM_API_KEY（大写 + 下划线）
"""

import os
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置。

    所有字段都可以通过环境变量覆盖。
    例如：export LLM_API_KEY="sk-xxx" 会自动填充 llm_api_key 字段。
    如果 .env 文件中也有这个变量，环境变量优先。
    """

    # LLM 配置 —— 用于调用大语言模型（Qwen 等）
    llm_api_key: SecretStr  # 必填，没有默认值，启动时必须提供
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # API 地址
    llm_model: str = "qwen-plus"  # 模型名称

    # Embedding 配置 —— 用于把文本转换为向量（数字数组），供 Milvus 做相似度搜索
    embedding_api_key: SecretStr
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v4"

    # Milvus 配置 —— 向量数据库，存储房源和知识库的 embedding
    milvus_uri: str = "http://localhost:19530"
    milvus_token: str = ""

    # lease 后端工具接口配置 —— AptGuide 通过 HTTP 调用 Java 后端获取业务数据
    lease_base_url: str = "http://127.0.0.1:8081"
    lease_internal_token: SecretStr  # 必填，与 lease 服务端共享密钥
    lease_request_timeout_seconds: int = 10

    # Redis 配置 —— 用于存储会话状态（当前阶段用内存降级，后续切换到 Redis）
    redis_url: str = "redis://localhost:6379/1"

    # 应用配置
    app_env: str = "development"  # development / production
    app_debug: bool = True
    log_level: str = "INFO"

    # LangSmith 可观测性 —— 记录 LLM / Agent / eval trace
    # 同时维护 LANGSMITH_*（新 SDK）和 LANGCHAIN_*（旧版兼容）两套变量
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "aptguide"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "aptguide"

    # model_config 是 pydantic v2 的配置方式（v2 用 model_config 替代了 class Config）
    model_config = {
        "env_file": ".env",  # 从项目根目录的 .env 文件读取
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # 忽略 .env 中未定义的多余变量，不报错
    }


def _sync_langsmith_environment(loaded_settings: Settings) -> None:
    """把 pydantic-settings 解析的 LangSmith 值写回 os.environ，供 LangSmith/LangGraph SDK 自动读取。"""
    values = {
        "LANGSMITH_TRACING": str(loaded_settings.langsmith_tracing).lower(),
        "LANGSMITH_API_KEY": loaded_settings.langsmith_api_key,
        "LANGSMITH_PROJECT": loaded_settings.langsmith_project,
        "LANGCHAIN_TRACING_V2": str(loaded_settings.langchain_tracing_v2).lower(),
        "LANGCHAIN_API_KEY": loaded_settings.langchain_api_key,
        "LANGCHAIN_PROJECT": loaded_settings.langchain_project,
    }
    for key, value in values.items():
        if value:
            os.environ[key] = value


@lru_cache
def get_settings() -> Settings:
    loaded_settings = Settings()
    _sync_langsmith_environment(loaded_settings)
    return loaded_settings
