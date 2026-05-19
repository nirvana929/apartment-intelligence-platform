from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

TaskName = Literal["room_search", "kb_qa", "fallback"]
ValidationMode = Literal["none", "lease_required", "source_required"]
SourcePolicy = Literal["none", "source_required", "high_risk_source_required"]


class RetrievalPlan(BaseModel):
    task: TaskName
    raw_message: str
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    semantic_queries: list[str] = Field(default_factory=list)
    sparse_queries: list[str] = Field(default_factory=list)
    module_intent: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
    validation_mode: ValidationMode = "none"
    source_policy: SourcePolicy = "none"


class RoomCandidate(BaseModel):
    room_id: int
    apartment_id: int | None = None
    semantic_score: float = 0.0
    matched_query: str = ""
    recall_source: str = "vector"
    extra: dict[str, Any] = Field(default_factory=dict)


class ValidatedRoom(BaseModel):
    room_id: int
    apartment_id: int = 0
    apartment_name: str = ""
    room_number: str = ""
    district_id: int | None = None
    district_name: str = ""
    rent: int = 0
    payment_types: list[str] = Field(default_factory=list)
    lease_terms: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    is_appointable: bool = False
    semantic_score: float = 0.0
    matched_query: str = ""
    wechat_room_id: str = ""
    lease_room_id: int | None = None
    source_collection: str = ""
    source_record_id: str = ""
    lease_validation_status: str = "not_checked"
    evidence_level: str = "vector_only"


class PreferenceScore(BaseModel):
    room_id: int
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_preferences: list[str] = Field(default_factory=list)
    missing_preferences: list[str] = Field(default_factory=list)
    reason: str = ""


class RankedRoom(BaseModel):
    room_id: int
    apartment_id: int = 0
    apartment_name: str = ""
    room_number: str = ""
    district_name: str = ""
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
    preference_score: float = 0.0
    availability_score: float = 0.0
    matched_query: str = ""
    recommendation_reason: str = ""
    wechat_room_id: str = ""
    lease_room_id: int | None = None
    source_collection: str = ""
    source_record_id: str = ""
    lease_validation_status: str = "not_checked"
    evidence_level: str = "vector_only"


class KBSource(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    module: str
    content: str
    score: float
    risk_level: Literal["low", "medium", "high"] = "low"
    matched_query: str = ""
    recall_source: str = "dense"
