from __future__ import annotations

from typing import Any

from aptguide3.rag.room_identity import RoomIdentity
from aptguide3.rag.room_retrieval import retrieve_ranked_rooms
from aptguide3.rag.schemas import PreferenceScore, RetrievalPlan, ValidatedRoom


class StubEmbedding:
    def __init__(self, vectors: dict[str, list[float]] | None = None):
        self._vectors = vectors or {}
        self.default = [0.1] * 8

    def embed(self, text: str) -> list[float]:
        return self._vectors.get(text, self.default)


class StubVector:
    def __init__(self, hits: list[dict[str, Any]] | None = None):
        self._hits = hits or []
        self.calls: list[tuple] = []

    def search_rooms(
        self, vector: list[float], filters: dict[str, Any] | None = None, top_k: int = 50,
    ) -> list[dict[str, Any]]:
        self.calls.append((vector, filters, top_k))
        return self._hits

    def search_wechat_rooms(
        self, vector: list[float], filters: dict[str, Any] | None = None, top_k: int = 50,
    ) -> list[dict[str, Any]]:
        self.calls.append((vector, filters, top_k))
        return self._hits


class StubLease:
    def __init__(self, rooms: list[dict[str, Any]] | None = None):
        self._rooms = rooms or []
        self.calls: list[tuple] = []

    async def validate_rooms(self, room_ids: list[int], filters: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append((room_ids, filters))
        return self._rooms


class StubIdentityRepo:
    """Stub identity repository for testing."""

    def __init__(self, mappings: dict[tuple[str, str], RoomIdentity] | None = None):
        self._mappings = mappings or {}

    async def get_by_source(self, source_system: str, source_record_id: str) -> RoomIdentity | None:
        return self._mappings.get((source_system, source_record_id))


class StubScorer:
    def __init__(self, scores: dict[int, PreferenceScore] | None = None):
        self._scores = scores or {}
        self.calls: list[tuple] = []

    def score(
        self, raw_message: str, soft_preferences: list[str], rooms: list[ValidatedRoom],
    ) -> dict[int, PreferenceScore]:
        self.calls.append((raw_message, soft_preferences, rooms))
        if self._scores:
            return self._scores
        return {room.room_id: PreferenceScore(room_id=room.room_id, score=0.5) for room in rooms}


def _plan(task: str = "room_search", **kwargs: Any) -> RetrievalPlan:
    defaults = dict(task=task, raw_message="找天河区的房子")
    defaults.update(kwargs)
    return RetrievalPlan(**defaults)


def _wechat_hit(room_id: int, **overrides: Any) -> dict[str, Any]:
    """Build a standard wechat vector hit with identity fields."""
    defaults = {
        "room_id": room_id,
        "apartment_id": 10,
        "distance": 0.2,
        "apartment_name": "天河公寓",
        "district_name": "天河区",
        "rent": 1500,
        "payment_types": ["月付"],
        "tags": [],
        "facilities": [],
        "wechat_room_id": f"wx_{room_id}",
        "lease_room_id": None,
        "source_collection": "wechat_room_index",
        "source_record_id": f"wx_{room_id}",
        "identity_mapping_status": "unmapped",
    }
    defaults.update(overrides)
    return defaults


def test_returns_empty_for_non_room_search_task():
    plan = _plan(task="kb_qa")
    result = retrieve_ranked_rooms(plan, StubVector(), StubEmbedding(), StubLease(), StubScorer())
    assert result == []


def test_returns_empty_when_embedding_fails():
    class FailEmbedding:
        def embed(self, text: str) -> list[float]:
            return []

    plan = _plan(semantic_queries=["天河租房"])
    result = retrieve_ranked_rooms(plan, StubVector(), FailEmbedding(), StubLease(), StubScorer())
    assert result == []


def test_returns_empty_when_vector_returns_no_hits():
    plan = _plan(semantic_queries=["天河租房"])
    result = retrieve_ranked_rooms(plan, StubVector(hits=[]), StubEmbedding(), StubLease(), StubScorer())
    assert result == []


def test_wechat_results_without_lease_id_are_vector_only():
    """Wechat data without lease_room_id gets vector_only evidence level."""
    plan = _plan(semantic_queries=["天河租房"])
    vector = StubVector(hits=[_wechat_hit(1)])
    result = retrieve_ranked_rooms(plan, vector, StubEmbedding(), StubLease(), StubScorer())
    assert len(result) == 1
    assert result[0].room_id == 1
    assert result[0].evidence_level == "vector_only"
    assert result[0].lease_validation_status == "not_checked"
    assert result[0].wechat_room_id == "wx_1"


def test_lease_validation_called_when_identity_verified():
    """When identity_repo returns a verified identity, lease validation is called."""
    plan = _plan(semantic_queries=["天河租房"])
    hit = _wechat_hit(1, lease_room_id=100, source_record_id="wx_1")
    vector = StubVector(hits=[hit])
    lease = StubLease(rooms=[{"room_id": 100}])
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx_1",
        business_room_id="100",
        verification_status="verified",
    )
    identity_repo = StubIdentityRepo(mappings={("wechat", "wx_1"): identity})

    result = retrieve_ranked_rooms(
        plan, vector, StubEmbedding(), lease, StubScorer(),
        identity_repo=identity_repo,
    )
    assert len(result) == 1
    assert result[0].evidence_level == "lease_validated"
    assert result[0].lease_validation_status == "passed"
    assert result[0].lease_room_id == 100
    # Verify lease was called with the business room ID
    assert len(lease.calls) == 1
    assert lease.calls[0][0] == [100]


def test_missing_lease_room_id_produces_vector_only():
    """When lease_room_id is missing and no identity repo, evidence_level is vector_only."""
    from aptguide3.rag.diagnostics import RoomRecDiagnostic

    plan = _plan(semantic_queries=["天河租房"])
    hit = _wechat_hit(1, lease_room_id=None)
    vector = StubVector(hits=[hit])
    diagnostic = RoomRecDiagnostic()

    result = retrieve_ranked_rooms(
        plan, vector, StubEmbedding(), StubLease(), StubScorer(),
        diagnostic=diagnostic,
    )
    assert len(result) == 1
    assert result[0].evidence_level == "vector_only"
    assert result[0].lease_validation_status == "not_checked"
    assert diagnostic.wechat_hits_without_lease_id_count == 1


def test_identity_repo_unverified_identity_is_wechat_only():
    """When identity is mapped_candidate, result is vector_only (not lease-validated)."""
    plan = _plan(semantic_queries=["天河租房"])
    hit = _wechat_hit(1, lease_room_id=100, source_record_id="wx_1")
    vector = StubVector(hits=[hit])
    lease = StubLease(rooms=[])
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx_1",
        business_room_id="100",
        verification_status="candidate",
    )
    identity_repo = StubIdentityRepo(mappings={("wechat", "wx_1"): identity})

    result = retrieve_ranked_rooms(
        plan, vector, StubEmbedding(), lease, StubScorer(),
        identity_repo=identity_repo,
    )
    assert len(result) == 1
    assert result[0].evidence_level == "mapped_candidate"
    assert result[0].lease_validation_status == "not_checked"
    # Lease should NOT be called for non-verified identities
    assert len(lease.calls) == 0


def test_evidence_fields_on_room_cards():
    """Room results carry all evidence fields."""
    plan = _plan(semantic_queries=["天河租房"])
    hit = _wechat_hit(1, lease_room_id=None, source_collection="wechat_room_index")
    vector = StubVector(hits=[hit])

    result = retrieve_ranked_rooms(plan, vector, StubEmbedding(), StubLease(), StubScorer())
    assert len(result) == 1
    room = result[0]
    assert room.wechat_room_id == "wx_1"
    assert room.source_collection == "wechat_room_index"
    assert room.source_record_id == "wx_1"
    assert room.evidence_level == "vector_only"
    assert room.lease_validation_status == "not_checked"


def test_returns_ranked_rooms_with_all_stubs():
    plan = _plan(
        semantic_queries=["天河租房"],
        hard_filters={"max_rent": 2000, "district_id": 10},
        soft_preferences=["安静"],
    )
    vector = StubVector(hits=[
        _wechat_hit(1, tags=["安静"], facilities=["空调"], distance=0.1),
        _wechat_hit(2, distance=0.3, apartment_name="番禺公寓", district_name="番禺区", rent=1800),
    ])
    lease = StubLease(rooms=[])
    scorer = StubScorer(scores={
        1: PreferenceScore(room_id=1, score=0.8, reason="安静偏好匹配"),
        2: PreferenceScore(room_id=2, score=0.4, reason="不太安静"),
    })

    result = retrieve_ranked_rooms(plan, vector, StubEmbedding(), lease, scorer, top_n=5)

    assert len(result) == 2
    assert result[0].final_score >= result[1].final_score
    assert result[0].room_id == 1


def test_deduplicates_rooms_across_queries():
    plan = _plan(semantic_queries=["天河", "天河区租房"])
    hits = [_wechat_hit(1, distance=0.1)]
    vector = StubVector(hits=hits)
    lease = StubLease(rooms=[])
    result = retrieve_ranked_rooms(plan, vector, StubEmbedding(), lease, StubScorer(), top_n=5)
    assert len(result) == 1


def test_top_n_limits_results():
    plan = _plan(semantic_queries=["租房"])
    hits = [_wechat_hit(i, distance=0.1) for i in range(1, 11)]
    vector = StubVector(hits=hits)
    lease = StubLease(rooms=[])
    result = retrieve_ranked_rooms(plan, vector, StubEmbedding(), lease, StubScorer(), top_n=3)
    assert len(result) == 3
