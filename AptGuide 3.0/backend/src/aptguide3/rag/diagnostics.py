from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RoomRecDiagnostic:
    task: str = "room_search"
    raw_message: str = ""
    semantic_queries: list[str] = field(default_factory=list)
    hard_filters: dict[str, Any] = field(default_factory=dict)
    soft_preferences: list[str] = field(default_factory=list)
    embedding_queries_attempted: int = 0
    embedding_empty_count: int = 0
    vector_hits_total: int = 0
    vector_unique_room_count: int = 0
    vector_top_room_ids: list[int] = field(default_factory=list)
    lease_validation_requested_count: int = 0
    lease_validated_count: int = 0
    lease_validation_failed_count: int = 0
    lease_dropped_room_ids: list[int] = field(default_factory=list)
    wechat_hits_without_lease_id_count: int = 0
    demo_fallback_count: int = 0
    preference_scored_count: int = 0
    ranked_count: int = 0
    final_room_ids: list[int] = field(default_factory=list)
    score_breakdown: list[dict[str, Any]] = field(default_factory=list)
    failure_stage: str = ""
    resolution_notes: list[str] = field(default_factory=list)
    # --- identity mapping diagnostics ---
    source_record_ids: list[str] = field(default_factory=list)
    identity_mapping_status_counts: dict[str, int] = field(default_factory=dict)
    mapped_verified_count: int = 0
    mapped_candidate_count: int = 0
    unmapped_count: int = 0
    synthetic_id_used_count: int = 0

    def to_report_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KbRecDiagnostic:
    task: str = "kb_qa"
    raw_message: str = ""
    semantic_queries: list[str] = field(default_factory=list)
    module_intent: str | None = None
    risk_level: str = "low"
    embedding_queries_attempted: int = 0
    embedding_empty_count: int = 0
    vector_hits_total: int = 0
    unique_chunk_count: int = 0
    returned_doc_ids: list[str] = field(default_factory=list)
    returned_chunk_ids: list[str] = field(default_factory=list)
    top_sources: list[dict[str, Any]] = field(default_factory=list)
    confidence_passed: bool | None = None
    confidence_failure_reason: str = ""
    failure_stage: str = ""

    def to_report_dict(self) -> dict[str, Any]:
        return asdict(self)
