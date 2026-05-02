import os
from unittest.mock import patch


def test_settings_load_from_env():
    with patch.dict(
        os.environ,
        {
            "LLM_API_KEY": "test_key",
            "LLM_BASE_URL": "https://test.api.com/v1",
            "LLM_MODEL": "qwen-plus",
            "EMBEDDING_API_KEY": "test_key",
            "MILVUS_URI": "http://localhost:19530",
        },
    ):
        from aptguide.core.config import Settings

        settings = Settings()
        assert settings.llm_api_key.get_secret_value() == "test_key"
        assert settings.llm_model == "qwen-plus"
        assert settings.milvus_uri == "http://localhost:19530"


def test_settings_default_values():
    with patch.dict(
        os.environ,
        {
            "LLM_API_KEY": "test_key",
            "EMBEDDING_API_KEY": "test_key",
        },
    ):
        from aptguide.core.config import Settings

        settings = Settings()
        assert settings.llm_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert settings.llm_model == "qwen-plus"
        assert settings.app_env == "development"
