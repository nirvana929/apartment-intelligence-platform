"""RAG Pydantic schemas for AptGuide 2.0 retrieval layer."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Risk Detection Types
# ---------------------------------------------------------------------------

RiskLevel = Literal["low", "medium", "high"]
RiskTopic = Literal[
    "room_search",
    "deposit_refund",
    "contract_termination",
    "complaint_escalation",
    "privacy_access",
    "normal_policy",
    "language_question",
    "unknown",
]
RiskAction = Literal[
    "ask_policy",
    "query_status",
    "request_action",
    "dispute",
    "escalation",
    "unauthorized_query",
    "ask_definition",
    "unknown",
]
ResponseMode = Literal[
    "normal_answer",
    "kb_grounded_answer",
    "authenticated_tool_query",
    "template_answer",
    "handoff_to_human",
    "refuse",
    "ask_clarification",
]


class RiskSignalScan(BaseModel):
    """Deterministic risk signals from rule scanning."""

    rule_signals: list[str] = Field(default_factory=list)
    hard_constraints: list[str] = Field(default_factory=list)
    non_downgrade_level: RiskLevel | None = None
    force_semantic_classifier: bool = False


class RiskClassifierResult(BaseModel):
    """Structured semantic classification of risk intent."""

    topic: RiskTopic = "unknown"
    action: RiskAction = "unknown"
    object: str = ""
    attitude: str = "neutral"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""


class RiskProfile(BaseModel):
    """Final risk decision used for routing, confidence gates, and response control."""

    topic: RiskTopic = "unknown"
    action: RiskAction = "unknown"
    object: str = ""
    attitude: str = "neutral"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_level: RiskLevel = "low"
    response_mode: ResponseMode = "normal_answer"
    rule_signals: list[str] = Field(default_factory=list)
    hard_constraints: list[str] = Field(default_factory=list)
    reason: str = ""


# ---------------------------------------------------------------------------
# Query Understanding
# ---------------------------------------------------------------------------

class QueryUnderstandingResult(BaseModel):
    """Output of the deterministic query understanding parser."""

    raw_message: str
    task: Literal["room_search", "kb_qa", "fallback"]
    domain: str = "unknown"
    reference_resolution: dict[str, Any] | None = None
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    retrieval_queries: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = "low"
    response_mode: ResponseMode = "normal_answer"
    risk_profile: RiskProfile = Field(default_factory=RiskProfile)


# ---------------------------------------------------------------------------
# Vector Records
# ---------------------------------------------------------------------------

class RoomVectorRecord(BaseModel):
    """A room record stored in the apt_room_vector Milvus collection."""

    vector_id: str
    room_id: int
    apartment_id: int
    apartment_name: str = ""
    city_id: int | None = None
    district_id: int | None = None
    district_name: str | None = None
    rent: int | None = None
    payment_types: list[str] = Field(default_factory=list)
    lease_terms: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    profile_type: Literal["room", "apartment", "audience"] = "room"
    content: str
    content_hash: str
    source_version: int
    status: Literal["active", "inactive"] = "active"


class KBChunk(BaseModel):
    """A knowledge base chunk stored in the apt_rental_kb Milvus collection."""

    chunk_id: str
    doc_id: str
    doc_type: str
    module: str
    title: str
    tags: list[str] = Field(default_factory=list)
    content: str
    content_hash: str
    version: int
    release_id: str
    status: Literal["candidate", "reviewed", "indexed", "evaluated", "active", "inactive"]
    risk_level: Literal["low", "medium", "high"] = "low"


# ---------------------------------------------------------------------------
# Retrieval Results
# ---------------------------------------------------------------------------

class RoomCandidate(BaseModel):
    """A room candidate from vector recall before lease validation."""

    room_id: int
    apartment_id: int | None = None
    semantic_score: float = 0.0
    matched_query: str = ""
    recall_source: str = "vector"


class ValidatedRoom(BaseModel):
    """A room that has been validated through lease."""

    room_id: int
    apartment_id: int
    apartment_name: str = ""
    room_number: str = ""
    rent: int = 0
    payment_types: list[str] = Field(default_factory=list)
    lease_terms: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    is_appointable: bool = False
    semantic_score: float = 0.0
    matched_query: str = ""


class RankedRoom(BaseModel):
    """A room after fine ranking."""

    room_id: int
    apartment_id: int
    apartment_name: str = ""
    room_number: str = ""
    rent: int = 0
    payment_types: list[str] = Field(default_factory=list)
    lease_terms: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    is_appointable: bool = False
    final_score: float = 0.0
    semantic_score: float = 0.0
    budget_score: float = 0.0
    area_score: float = 0.0
    tag_score: float = 0.0
    availability_score: float = 0.0
    matched_query: str = ""
    recommendation_reason: str = ""


# ---------------------------------------------------------------------------
# KB Results
# ---------------------------------------------------------------------------

class KBSource(BaseModel):
    """A knowledge source returned from KB retrieval."""

    chunk_id: str
    doc_id: str
    title: str
    module: str
    content: str
    score: float
    risk_level: Literal["low", "medium", "high"] = "low"
    matched_query: str = ""
    recall_source: str = "original"


# ---------------------------------------------------------------------------
# Pipeline Result
# ---------------------------------------------------------------------------


class PipelineResult(BaseModel):
    """Structured result from the RAG pipeline."""

    task: Literal["room_search", "kb_qa", "fallback"]
    message: str = ""
    rooms: list[RankedRoom] = Field(default_factory=list)
    kb_sources: list[KBSource] = Field(default_factory=list)
    is_confident: bool = False
    fallback_reason: str = ""
    query_understanding: QueryUnderstandingResult | None = None


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

class RetrievalLatency(BaseModel):
    """Latency breakdown for a retrieval operation."""

    rewrite_latency_ms: float = 0.0
    embedding_latency_ms: float = 0.0
    vector_search_latency_ms: float = 0.0
    merge_latency_ms: float = 0.0
    lease_validation_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0
    retrieval_total_latency_ms: float = 0.0


class RetrievalTracePayload(BaseModel):
    """Payload for the retrieval_finished trace event."""

    task: Literal["room_search", "kb_qa", "fallback"]
    rewrite_count: int = 0
    collections: list[str] = Field(default_factory=list)
    top_k: int = 0
    filters: dict[str, Any] = Field(default_factory=dict)
    candidate_count: int = 0
    validated_count: int = 0
    latency: RetrievalLatency = Field(default_factory=RetrievalLatency)


# ---------------------------------------------------------------------------
# Eval
# ---------------------------------------------------------------------------

class RetrievalEvalCase(BaseModel):
    """A single retrieval evaluation case."""

    case_id: str
    case_type: Literal["room_retrieval", "kb_retrieval", "fallback_retrieval"]
    query: str
    expected_room_ids: list[int] = Field(default_factory=list)
    expected_doc_ids: list[str] = Field(default_factory=list)
    expected_task: Literal["room_search", "kb_qa", "fallback"] = "room_search"
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
