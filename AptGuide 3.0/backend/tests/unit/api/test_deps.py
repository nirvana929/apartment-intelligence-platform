"""Tests for persistence-mode wiring in deps.py.

All tests run WITHOUT live MySQL or Redis.
"""
from __future__ import annotations

import pytest

from aptguide3.api import deps
from aptguide3.api.deps import RepoBundle
from aptguide3.config import Settings
from aptguide3.persistence.handoff_repo import InMemoryHandoffRepo
from aptguide3.persistence.memory_repo import InMemoryMemoryRepo
from aptguide3.persistence.pending_action_repo import InMemoryPendingActionRepo
from aptguide3.persistence.session_repo import InMemorySessionRepo
from aptguide3.rag.preference_scorer import LLMPreferenceScorer


@pytest.fixture(autouse=True)
def _clear_chat_service_cache():
    """Clear lru_cache between tests so settings changes take effect."""
    deps.get_chat_service.cache_clear()
    yield
    deps.get_chat_service.cache_clear()


def _settings(**overrides) -> Settings:
    """Build Settings with safe defaults + overrides."""
    base = dict(
        llm_api_key="",
        embedding_api_key="",
        persistence_mode="memory",
        mysql_dsn="mysql+asyncmy://root:change-me@localhost:3306/aptguide3",
        redis_url="",
    )
    base.update(overrides)
    return Settings(**base)


# -- RepoBundle type checks ----------------------------------------------------

def test_repo_bundle_has_all_eight_fields():
    """RepoBundle must expose all 8 repository slots."""
    bundle = RepoBundle(
        session_repo="a", message_repo="b", pending_action_repo="c",
        memory_repo="d", handoff_repo="e", trace_repo="f",
        procedure_run_repo="g", audit_repo="h",
    )
    assert bundle.session_repo == "a"
    assert bundle.message_repo == "b"
    assert bundle.pending_action_repo == "c"
    assert bundle.memory_repo == "d"
    assert bundle.handoff_repo == "e"
    assert bundle.trace_repo == "f"
    assert bundle.procedure_run_repo == "g"
    assert bundle.audit_repo == "h"


# -- memory mode (default) ---------------------------------------------------

def test_memory_mode_returns_repo_bundle():
    """_build_memory_repos must return a RepoBundle."""
    bundle = deps._build_memory_repos()
    assert isinstance(bundle, RepoBundle)


def test_memory_mode_in_memory_repos():
    """Memory mode must use InMemory* implementations where available."""
    bundle = deps._build_memory_repos()
    assert isinstance(bundle.session_repo, InMemorySessionRepo)
    assert isinstance(bundle.pending_action_repo, InMemoryPendingActionRepo)
    assert isinstance(bundle.memory_repo, InMemoryMemoryRepo)
    assert isinstance(bundle.handoff_repo, InMemoryHandoffRepo)


def test_memory_mode_none_for_unimplemented():
    """Memory mode must return None for repos without in-memory implementations."""
    bundle = deps._build_memory_repos()
    assert bundle.message_repo is None
    assert bundle.trace_repo is None
    assert bundle.procedure_run_repo is None
    assert bundle.audit_repo is None


def test_memory_mode_via_build_repos_dispatch():
    """_build_repos('memory') must delegate to _build_memory_repos."""
    settings = _settings(persistence_mode="memory")
    bundle = deps._build_repos(settings)
    assert isinstance(bundle, RepoBundle)
    assert isinstance(bundle.session_repo, InMemorySessionRepo)


def test_memory_mode_produces_in_memory_session_repo(monkeypatch):
    """Full integration: get_chat_service in memory mode uses InMemorySessionRepo."""
    monkeypatch.setenv("APTGUIDE3_PERSISTENCE_MODE", "memory")
    settings = _settings(persistence_mode="memory")
    monkeypatch.setattr(deps, "get_settings", lambda: settings)

    svc = deps.get_chat_service()
    assert isinstance(svc.session_repo, InMemorySessionRepo)
    assert svc.message_repo is None
    assert svc.procedure_run_repo is None


# -- mysql mode: no live DB needed at construction time -----------------------

def test_mysql_mode_returns_repo_bundle():
    """_build_mysql_repos must return a RepoBundle."""
    settings = _settings(persistence_mode="mysql")
    bundle = deps._build_mysql_repos(settings)
    assert isinstance(bundle, RepoBundle)


def test_mysql_mode_all_repos_non_none():
    """All 8 repos must be populated in MySQL mode."""
    settings = _settings(persistence_mode="mysql")
    bundle = deps._build_mysql_repos(settings)
    for field in (
        "session_repo", "message_repo", "pending_action_repo",
        "memory_repo", "handoff_repo", "trace_repo",
        "procedure_run_repo", "audit_repo",
    ):
        assert getattr(bundle, field) is not None, f"{field} must not be None in MySQL mode"


def test_mysql_mode_lazy_init_no_connection_required(monkeypatch):
    """Constructing repos in mysql mode must NOT open a connection.

    build_sessionmaker() only creates a sessionmaker/engine object;
    no TCP connection is opened until a session is actually used.
    """
    monkeypatch.setenv("APTGUIDE3_PERSISTENCE_MODE", "mysql")
    settings = _settings(persistence_mode="mysql")
    monkeypatch.setattr(deps, "get_settings", lambda: settings)

    # _build_mysql_repos should succeed without touching the network
    bundle = deps._build_mysql_repos(settings)
    assert bundle.session_repo is not None
    assert bundle.message_repo is not None
    assert bundle.procedure_run_repo is not None


# -- hybrid mode: no live DB/Redis needed at construction time ----------------

def test_hybrid_mode_returns_repo_bundle():
    """_build_hybrid_repos must return a RepoBundle."""
    settings = _settings(persistence_mode="hybrid", redis_url="redis://localhost:6379/0")
    bundle = deps._build_hybrid_repos(settings)
    assert isinstance(bundle, RepoBundle)


def test_hybrid_mode_all_repos_non_none():
    """All 8 repos must be populated in hybrid mode."""
    settings = _settings(persistence_mode="hybrid", redis_url="redis://localhost:6379/0")
    bundle = deps._build_hybrid_repos(settings)
    for field in (
        "session_repo", "message_repo", "pending_action_repo",
        "memory_repo", "handoff_repo", "trace_repo",
        "procedure_run_repo", "audit_repo",
    ):
        assert getattr(bundle, field) is not None, f"{field} must not be None in hybrid mode"


def test_hybrid_mode_lazy_init_no_connections_required(monkeypatch):
    monkeypatch.setenv("APTGUIDE3_PERSISTENCE_MODE", "hybrid")
    settings = _settings(persistence_mode="hybrid", redis_url="redis://localhost:6379/0")
    monkeypatch.setattr(deps, "get_settings", lambda: settings)

    bundle = deps._build_hybrid_repos(settings)
    assert bundle.session_repo is not None
    assert bundle.message_repo is not None
    assert bundle.procedure_run_repo is not None


def test_hybrid_mode_works_without_redis_url(monkeypatch):
    """hybrid mode with empty redis_url should still construct repos."""
    settings = _settings(persistence_mode="hybrid", redis_url="")
    bundle = deps._build_hybrid_repos(settings)
    assert bundle.session_repo is not None


# -- invalid mode -------------------------------------------------------------

def test_invalid_persistence_mode_raises_validation_error():
    with pytest.raises(Exception) as exc_info:
        _settings(persistence_mode="bogus")
    assert "persistence_mode" in str(exc_info.value).lower() or "bogus" in str(exc_info.value)


def test_build_repos_unknown_mode_raises_value_error():
    """_build_repos with an unrecognised mode must raise ValueError."""
    settings = _settings(persistence_mode="memory")
    # Monkey-patch the mode after construction to bypass Settings validation
    object.__setattr__(settings, "persistence_mode", "bogus")
    with pytest.raises(ValueError, match="Unknown persistence_mode"):
        deps._build_repos(settings)


# -- env var wiring -----------------------------------------------------------

def test_persistence_mode_reads_env_var(monkeypatch):
    monkeypatch.setenv("APTGUIDE3_PERSISTENCE_MODE", "mysql")
    settings = Settings()
    assert settings.persistence_mode == "mysql"


def test_persistence_mode_default_is_memory():
    settings = Settings()
    assert settings.persistence_mode == "memory"


# -- RAG dependency wiring ----------------------------------------------------

def test_rag_settings_have_defaults():
    settings = Settings()
    assert settings.rag_room_top_k == 30
    assert settings.rag_room_top_n == 5
    assert settings.rag_kb_top_k == 10
    assert settings.rag_preference_scorer_enabled is True


def test_build_runtime_wires_preference_scorer():
    settings = _settings(rag_preference_scorer_enabled=True)
    bundle = deps._build_memory_repos()
    runtime = deps.build_runtime(settings, bundle)
    room_proc = runtime._procedures["room_search"]
    assert isinstance(room_proc._preference_scorer, LLMPreferenceScorer)


def test_build_runtime_preference_scorer_disabled():
    settings = _settings(rag_preference_scorer_enabled=False)
    bundle = deps._build_memory_repos()
    runtime = deps.build_runtime(settings, bundle)
    room_proc = runtime._procedures["room_search"]
    assert isinstance(room_proc._preference_scorer, LLMPreferenceScorer)
    assert room_proc._preference_scorer.client is None


def test_build_runtime_room_search_has_vector_and_embedding():
    settings = _settings()
    bundle = deps._build_memory_repos()
    runtime = deps.build_runtime(settings, bundle)
    room_proc = runtime._procedures["room_search"]
    # Without embedding_api_key, vector/embedding clients are None
    assert room_proc._vector_client is None
    assert room_proc._embedding_client is None
