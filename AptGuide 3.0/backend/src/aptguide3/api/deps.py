from functools import lru_cache

from openai import OpenAI

from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.config import Settings, get_settings
from aptguide3.integrations.embedding_client import EmbeddingClient
from aptguide3.integrations.lease_client import LeaseClient
from aptguide3.integrations.vector_client import VectorClient
from aptguide3.observability.sink import ConsoleTraceSink
from aptguide3.observability.trace import Tracer
from aptguide3.persistence.session_repo import InMemorySessionRepo
from aptguide3.procedures.appointment import AppointmentProcedure
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.handoff import HandoffProcedure
from aptguide3.procedures.kb_qa import KbQaProcedure
from aptguide3.procedures.lease import LeaseProcedure
from aptguide3.procedures.memory import MemoryProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure
from aptguide3.understanding.llm_understanding import LLMUnderstanding
from aptguide3.understanding.validation import clarification_result


class ClarifyOnlyUnderstanding:
    def understand(self, message: str):
        return clarification_result(message, "llm_not_configured")


def get_llm_client(settings: Settings):
    if not settings.llm_api_key.get_secret_value():
        return None
    return OpenAI(api_key=settings.llm_api_key.get_secret_value(), base_url=settings.llm_base_url)


def get_lease_client(settings: Settings) -> LeaseClient:
    return LeaseClient(base_url=settings.lease_base_url, timeout=settings.lease_timeout_seconds)


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


def build_runtime(settings: Settings) -> ProcedureRuntime:
    vc, ec = get_kb_clients(settings)
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    runtime.register(RoomSearchProcedure(lease_client=get_lease_client(settings)))
    runtime.register(KbQaProcedure(vector_client=vc, embedding_client=ec))
    runtime.register(AppointmentProcedure())
    runtime.register(LeaseProcedure())
    runtime.register(MemoryProcedure())
    runtime.register(HandoffProcedure())
    return runtime


@lru_cache
def get_tracer() -> Tracer:
    return Tracer(ConsoleTraceSink())


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    client = get_llm_client(settings)
    understanding = (
        LLMUnderstanding(client, settings.llm_model, settings.understanding_min_confidence)
        if client is not None
        else ClarifyOnlyUnderstanding()
    )
    session_repo = InMemorySessionRepo()
    return ChatService(
        SafetyBoundary(), understanding, build_runtime(settings), session_repo=session_repo, tracer=get_tracer(),
    )
