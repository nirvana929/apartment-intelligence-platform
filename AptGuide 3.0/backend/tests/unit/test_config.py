from aptguide3.config import Settings, get_settings


def test_independent_backend_settings_defaults():
    settings = Settings()
    assert settings.auth_mode == "dev"
    assert settings.redis_key_prefix == "aptguide3"
    assert settings.session_ttl_seconds == 86400
    assert settings.pending_action_ttl_seconds == 300
    assert settings.mysql_dsn.startswith("mysql+asyncmy://")
    assert settings.internal_token_required is False


def test_langsmith_settings_default_off(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv("APTGUIDE3_LANGSMITH_TRACING", raising=False)
    settings = get_settings()

    assert settings.langsmith_tracing is False
    assert settings.langsmith_project == "aptguide3-local"
    assert settings.understanding_diagnostics_enabled is False
    get_settings.cache_clear()


def test_langsmith_settings_can_be_enabled(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("APTGUIDE3_LANGSMITH_TRACING", "true")
    monkeypatch.setenv("APTGUIDE3_LANGSMITH_PROJECT", "aptguide3-rag-debug")
    monkeypatch.setenv("APTGUIDE3_UNDERSTANDING_DIAGNOSTICS_ENABLED", "true")
    settings = get_settings()

    assert settings.langsmith_tracing is True
    assert settings.langsmith_project == "aptguide3-rag-debug"
    assert settings.understanding_diagnostics_enabled is True
    get_settings.cache_clear()
