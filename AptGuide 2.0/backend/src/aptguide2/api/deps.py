"""Dependency injection for the API."""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.modules.appointment import AppointmentWorkflowProcedure
from aptguide2.harness.modules.capability import CapabilityProcedure
from aptguide2.harness.modules.fallback import FallbackProcedure
from aptguide2.harness.modules.handoff import HandoffProcedure
from aptguide2.harness.modules.lease import LeaseWorkflowProcedure
from aptguide2.harness.modules.rag.v2 import RagV2Procedure
from aptguide2.harness.orchestrator import AptGuideHarness
from aptguide2.harness.procedures import ProcedureRuntime
from aptguide2.harness.routing import HybridRouter
from aptguide2.tools.vector_adapter import VectorAdapter


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_vector_adapter() -> VectorAdapter:
    s = get_settings()
    return VectorAdapter(
        uri=s.milvus_uri,
        token=s.milvus_token,
        dim=s.embedding_dim,
    )


def get_embed_fn():
    """Return a sync embed function for the current settings."""
    s = get_settings()
    client = OpenAI(
        api_key=s.embedding_api_key.get_secret_value(),
        base_url=s.embedding_base_url,
    )

    def embed(text: str) -> list[float]:
        resp = client.embeddings.create(model=s.embedding_model, input=[text])
        return resp.data[0].embedding

    return embed


def get_llm_client() -> OpenAI:
    """Return an OpenAI-compatible LLM client."""
    s = get_settings()
    return OpenAI(
        api_key=s.llm_api_key.get_secret_value(),
        base_url=s.llm_base_url,
    )


@lru_cache
def get_context_store() -> InMemoryContextStore:
    return InMemoryContextStore()


def get_aptguide_harness() -> AptGuideHarness:
    runtime = ProcedureRuntime()
    runtime.register("capability.profile", CapabilityProcedure())
    runtime.register("fallback.safety", FallbackProcedure())
    runtime.register("fallback.unknown", FallbackProcedure())
    rag = RagV2Procedure(
        vector_adapter=get_vector_adapter(),
        embed_fn=get_embed_fn(),
    )
    runtime.register("rag.room_search", rag)
    runtime.register("rag.kb_qa", rag)
    runtime.register("appointment.workflow", AppointmentWorkflowProcedure())
    runtime.register("lease.workflow", LeaseWorkflowProcedure())
    handoff = HandoffProcedure()
    runtime.register("handoff.user_initiated", handoff)
    runtime.register("handoff.tool_failure", handoff)
    settings = get_settings()
    return AptGuideHarness(
        context_store=get_context_store(),
        router=HybridRouter(),
        procedure_runtime=runtime,
        include_trace=settings.harness_include_trace,
        tool_runtime=get_tool_runtime(),
    )


from aptguide2.harness.tools.builtins import build_default_tool_registry
from aptguide2.harness.tools.lease_tools import (
    AppointmentCancelExecutor,
    AppointmentCreateExecutor,
    AppointmentListMineExecutor,
    LeaseHealthExecutor,
    LeaseListMineExecutor,
    RoomDetailExecutor,
    RoomSearchExecutor,
)
from aptguide2.harness.tools.runtime import ToolRuntime
from aptguide2.harness.tools.vector_tools import KBSearchExecutor


@lru_cache
def get_tool_runtime() -> ToolRuntime:
    registry = build_default_tool_registry()
    runtime = ToolRuntime(registry)

    adapter = get_vector_adapter()
    embed_fn = get_embed_fn()

    # Use a lazy lease adapter reference to avoid import issues
    # The lease adapter is constructed on first use
    lease_adapter = _get_lease_adapter()

    runtime.register_executor("lease.health", LeaseHealthExecutor(lease_adapter))
    runtime.register_executor("room.search", RoomSearchExecutor(lease_adapter))
    runtime.register_executor("room.detail", RoomDetailExecutor(lease_adapter))
    runtime.register_executor("kb.search", KBSearchExecutor(adapter, embed_fn))

    # Appointment/lease list executors - register with adapter, will return
    # TOOL_NOT_IMPLEMENTED if adapter lacks the method
    runtime.register_executor("appointment.create", AppointmentCreateExecutor(lease_adapter))
    runtime.register_executor("appointment.list_mine", AppointmentListMineExecutor(lease_adapter))
    runtime.register_executor("appointment.cancel", AppointmentCancelExecutor(lease_adapter))
    runtime.register_executor("lease.list_mine", LeaseListMineExecutor(lease_adapter))

    # trace.record has no executor registered - it will return TOOL_NOT_IMPLEMENTED
    # which is correct since trace recording is handled by the harness TraceRecorder

    return runtime


def _get_lease_adapter():
    """Lazy lease adapter construction."""
    from aptguide2.tools.lease_adapter import LeaseAdapter
    s = get_settings()
    return LeaseAdapter(
        base_url=s.lease_base_url,
        timeout=s.lease_timeout_seconds,
        internal_token=s.lease_internal_token,
    )
