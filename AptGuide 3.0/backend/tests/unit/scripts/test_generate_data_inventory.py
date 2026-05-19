from scripts.generate_data_inventory import _is_sensitive, _redact_value, _sanitize_config


def test_is_sensitive_detects_api_key():
    assert _is_sensitive("api_key") is True
    assert _is_sensitive("llm_api_key") is True
    assert _is_sensitive("mysql_dsn") is True
    assert _is_sensitive("password") is True
    assert _is_sensitive("internal_token") is True


def test_is_sensitive_allows_safe_keys():
    assert _is_sensitive("llm_model") is False
    assert _is_sensitive("service_name") is False
    assert _is_sensitive("vector_uri") is False
    assert _is_sensitive("persistence_mode") is False


def test_redact_value_redacts_sensitive():
    assert _redact_value("api_key", "sk-secret123") == "<redacted>"
    assert _redact_value("mysql_dsn", "mysql://user:pass@host/db") == "<redacted>"


def test_redact_value_preserves_safe():
    assert _redact_value("model", "qwen-turbo") == "qwen-turbo"
    assert _redact_value("count", 42) == 42


def test_sanitize_config_redacts_secrets():
    from types import SimpleNamespace

    settings = SimpleNamespace(
        environment="local",
        service_name="aptguide3",
        llm_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        llm_model="qwen-turbo-latest",
        embedding_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        embedding_model="text-embedding-v3",
        lease_base_url="http://localhost:8081",
        vector_uri="http://localhost:19530",
        auth_mode="dev",
        persistence_mode="hybrid",
        redis_url="redis://localhost:6379/3",
        langsmith_tracing=False,
        langsmith_project="aptguide3-local",
        understanding_diagnostics_enabled=False,
    )

    result = _sanitize_config(settings)

    assert result["environment"] == "local"
    assert result["llm_model"] == "qwen-turbo-latest"
    assert result["redis_url"] == "<set>"
    assert "api_key" not in result or result.get("api_key") == "<redacted>"
