from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from openai import OpenAI

from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.config import Settings, get_settings
from aptguide3.integrations.embedding_client import EmbeddingClient
from aptguide3.integrations.lease_client import LeaseClient
from aptguide3.integrations.vector_client import VectorClient
from aptguide3.observability.langsmith_trace import LangSmithChatRecorder
from aptguide3.observability.repository_sink import RepositoryTraceSink
from aptguide3.observability.sink import ConsoleTraceSink
from aptguide3.observability.trace import Tracer
from aptguide3.persistence.handoff_repo import InMemoryHandoffRepo
from aptguide3.persistence.memory_repo import InMemoryMemoryRepo
from aptguide3.persistence.pending_action_repo import InMemoryPendingActionRepo
from aptguide3.persistence.session_repo import InMemorySessionRepo
from aptguide3.procedures.appointment import AppointmentProcedure
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.handoff import HandoffProcedure
from aptguide3.procedures.kb_qa import KbQaProcedure
from aptguide3.procedures.lease import LeaseProcedure
from aptguide3.procedures.memory import MemoryProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure
from aptguide3.rag.preference_scorer import LLMPreferenceScorer
from aptguide3.understanding.llm_understanding import LLMUnderstanding
from aptguide3.understanding.validation import clarification_result

logger = logging.getLogger(__name__)


@dataclass
class RepoBundle:
    """Container for all 8 repository types required by the runtime."""

    session_repo: Any
    message_repo: Any
    pending_action_repo: Any
    memory_repo: Any
    handoff_repo: Any
    trace_repo: Any
    procedure_run_repo: Any
    audit_repo: Any
    room_identity_repo: Any = None


class ClarifyOnlyUnderstanding:
    def understand(self, message: str):
        return clarification_result(message, "llm_not_configured")


def _maybe_wrap_langsmith(client, settings):
    if not settings.langsmith_tracing:
        return client
    try:
        from langsmith.wrappers import wrap_openai
    except ImportError:
        return client
    return wrap_openai(
        client,
        tracing_extra={
            "project_name": settings.langsmith_project,
            "metadata": {
                "service": settings.service_name,
                "environment": settings.environment,
            },
            "tags": ["aptguide3", "understanding"],
        },
    )


def get_llm_client(settings: Settings):
    if not settings.llm_api_key.get_secret_value():
        return None
    client = OpenAI(api_key=settings.llm_api_key.get_secret_value(), base_url=settings.llm_base_url)
    client = _maybe_wrap_langsmith(client, settings)
    return client


def get_lease_client(settings: Settings) -> LeaseClient:
    return LeaseClient(
        base_url=settings.lease_base_url,
        timeout=settings.lease_timeout_seconds,
        internal_token=settings.internal_token.get_secret_value(),
    )


def get_kb_clients(settings: Settings) -> tuple[VectorClient | None, EmbeddingClient | None]:
    if not settings.embedding_api_key.get_secret_value():
        return None, None
    try:
        vc = VectorClient(uri=settings.vector_uri)
        ec = EmbeddingClient(
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key.get_secret_value(),
            model=settings.embedding_model,
        )
        return vc, ec
    except Exception:
        return None, None


def build_runtime(settings: Settings, bundle: RepoBundle) -> ProcedureRuntime:
    vc, ec = get_kb_clients(settings)
    lease = get_lease_client(settings)
    llm_client = get_llm_client(settings)
    preference_scorer = (
        LLMPreferenceScorer(llm_client, settings.llm_model)
        if settings.rag_preference_scorer_enabled and llm_client is not None
        else LLMPreferenceScorer(None, settings.llm_model)
    )
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    runtime.register(RoomSearchProcedure(
        lease_client=lease,
        vector_client=vc,
        embedding_client=ec,
        preference_scorer=preference_scorer,
        identity_repo=bundle.room_identity_repo,
    ))
    runtime.register(KbQaProcedure(vector_client=vc, embedding_client=ec))
    runtime.register(AppointmentProcedure(
        pending_action_repo=bundle.pending_action_repo,
        lease_client=lease,
        audit_repo=bundle.audit_repo,
    ))
    runtime.register(LeaseProcedure(lease_client=lease, audit_repo=bundle.audit_repo))
    runtime.register(MemoryProcedure(memory_repo=bundle.memory_repo))
    runtime.register(HandoffProcedure(handoff_repo=bundle.handoff_repo, audit_repo=bundle.audit_repo))
    return runtime


@lru_cache
def get_tracer() -> Tracer:
    return Tracer(ConsoleTraceSink())


def _build_memory_repos() -> RepoBundle:
    """Return a RepoBundle with in-memory implementations where available."""
    from aptguide3.persistence.room_identity_repo import InMemoryRoomIdentityRepository
    return RepoBundle(
        session_repo=InMemorySessionRepo(),
        message_repo=None,
        pending_action_repo=InMemoryPendingActionRepo(),
        memory_repo=InMemoryMemoryRepo(),
        handoff_repo=InMemoryHandoffRepo(),
        trace_repo=None,
        procedure_run_repo=None,
        audit_repo=None,
        room_identity_repo=InMemoryRoomIdentityRepository(),
    )


def _build_mysql_repos(settings: Settings) -> RepoBundle:
    """Return a RepoBundle with all 8 MySQL repository implementations."""
    from aptguide3.database.database import build_sessionmaker
    from aptguide3.persistence.mysql_repos import (
        MySqlAuditRepository,
        MySqlHandoffRepository,
        MySqlMemoryRepository,
        MySqlMessageRepository,
        MySqlPendingActionRepository,
        MySqlProcedureRunRepository,
        MySqlRoomIdentityRepository,
        MySqlSessionRepository,
        MySqlTraceRepository,
    )

    sm = build_sessionmaker(settings.mysql_dsn)
    return RepoBundle(
        session_repo=MySqlSessionRepository(sm),
        message_repo=MySqlMessageRepository(sm),
        pending_action_repo=MySqlPendingActionRepository(sm),
        memory_repo=MySqlMemoryRepository(sm),
        handoff_repo=MySqlHandoffRepository(sm),
        trace_repo=MySqlTraceRepository(sm),
        procedure_run_repo=MySqlProcedureRunRepository(sm),
        audit_repo=MySqlAuditRepository(sm),
        room_identity_repo=MySqlRoomIdentityRepository(sm),
    )


def _build_hybrid_repos(settings: Settings) -> RepoBundle:
    """Return a RepoBundle with all 8 MySQL repository implementations for hybrid mode.

    MySQL repos for durable state; RedisStateStore is created but attached
    separately when the chat service / procedures support it.
    """
    from aptguide3.database.database import build_sessionmaker
    from aptguide3.persistence.mysql_repos import (
        MySqlAuditRepository,
        MySqlHandoffRepository,
        MySqlMemoryRepository,
        MySqlMessageRepository,
        MySqlPendingActionRepository,
        MySqlProcedureRunRepository,
        MySqlRoomIdentityRepository,
        MySqlSessionRepository,
        MySqlTraceRepository,
    )

    sm = build_sessionmaker(settings.mysql_dsn)

    # Pre-create the Redis store for future use; log availability.
    if settings.redis_url:
        logger.info("hybrid mode: redis_url configured, RedisStateStore available for hot-state caching")
    else:
        logger.warning("hybrid mode: redis_url is empty, hot-state caching disabled")

    return RepoBundle(
        session_repo=MySqlSessionRepository(sm),
        message_repo=MySqlMessageRepository(sm),
        pending_action_repo=MySqlPendingActionRepository(sm),
        memory_repo=MySqlMemoryRepository(sm),
        handoff_repo=MySqlHandoffRepository(sm),
        trace_repo=MySqlTraceRepository(sm),
        procedure_run_repo=MySqlProcedureRunRepository(sm),
        audit_repo=MySqlAuditRepository(sm),
        room_identity_repo=MySqlRoomIdentityRepository(sm),
    )


def _build_repos(settings: Settings) -> RepoBundle:
    """Select persistence repos based on settings.persistence_mode."""
    mode = settings.persistence_mode
    if mode == "memory":
        return _build_memory_repos()
    if mode == "mysql":
        return _build_mysql_repos(settings)
    if mode == "hybrid":
        return _build_hybrid_repos(settings)
    raise ValueError(f"Unknown persistence_mode: {mode!r}")


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    client = get_llm_client(settings)
    understanding = (
        LLMUnderstanding(
            client,
            settings.llm_model,
            settings.understanding_min_confidence,
            diagnostics_enabled=settings.understanding_diagnostics_enabled,
        )
        if client is not None
        else ClarifyOnlyUnderstanding()
    )
    bundle = _build_repos(settings)
    tracer = (
        Tracer(RepositoryTraceSink(bundle.trace_repo))
        if bundle.trace_repo is not None
        else get_tracer()
    )
    recorder = LangSmithChatRecorder(
        enabled=settings.langsmith_tracing,
        project_name=settings.langsmith_project,
        service_name=settings.service_name,
        environment=settings.environment,
    )
    return ChatService(
        SafetyBoundary(), understanding, build_runtime(settings, bundle),
        session_repo=bundle.session_repo, tracer=tracer,
        message_repo=bundle.message_repo,
        procedure_run_repo=bundle.procedure_run_repo,
        langsmith_recorder=recorder,
    )
