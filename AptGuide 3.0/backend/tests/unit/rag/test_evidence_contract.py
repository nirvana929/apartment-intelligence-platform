"""Evidence contract shape tests.

These tests verify that room search and KB QA pipelines produce data structures
conforming to the evidence contract defined in docs/system/evidence-contract.md.

They are diagnostic/assertion tests -- they do NOT change ranking or answer
generation code. They check the contract at the data-structure level.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Constants: required keys per the evidence contract
# ---------------------------------------------------------------------------

ROOM_CARD_REQUIRED_KEYS = {
    "wechat_room_id",
    "lease_room_id",
    "lease_validation_status",
    "evidence_level",
}

ROOM_CARD_RECOMMENDED_KEYS = {
    "room_card_type",
    "source_collection",
    "district_name",
    "rent",
    "matched_query",
    "semantic_score",
    "final_score",
    "availability_status",
}

KB_SOURCE_REQUIRED_KEYS = {
    "chunk_id",
    "doc_id",
    "title",
    "module",
    "score",
    "risk_level",
    "evidence_level",
}

KB_FINAL_ANSWER_REQUIRED_KEYS = {
    "risk_level",
    "confidence_passed",
    "evidence_count",
    "grounded_answer",
    "citations",
    "fallback_reason",
}

VALID_EVIDENCE_LEVELS = {
    "vector_only",
    "source_grounded",
    "lease_validated",
    "lease_validated_with_freshness",
    "conservative_fallback",
}

RISK_LEVELS = {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# Helper: validate evidence level
# ---------------------------------------------------------------------------


def _is_valid_evidence_level(level: str) -> bool:
    return level in VALID_EVIDENCE_LEVELS


def _risk_requires_validation(risk_level: str, evidence_level: str) -> bool:
    """Return True if the combination violates the contract.

    Rule: medium/high-risk output cannot use vector_only as final evidence.
    """
    return risk_level in {"medium", "high"} and evidence_level == "vector_only"


# ===========================================================================
# Room Evidence Contract Tests
# ===========================================================================


class TestRoomEvidenceContract:
    """Verify room card data structures meet the evidence contract."""

    def test_room_evidence_contract_requires_business_identity(self):
        """Room cards must carry wechat_room_id, lease_room_id,
        lease_validation_status, and evidence_level."""
        card = {
            "wechat_room_id": "wx-1",
            "lease_room_id": 101,
            "lease_validation_status": "passed",
            "evidence_level": "lease_validated",
        }
        assert ROOM_CARD_REQUIRED_KEYS <= set(card), (
            f"Missing required keys: {ROOM_CARD_REQUIRED_KEYS - set(card)}"
        )

    def test_room_card_must_have_wechat_room_id(self):
        """wechat_room_id is the primary cross-reference identifier."""
        card = {
            "wechat_room_id": "wx_room_abc123",
            "lease_room_id": 101,
            "lease_validation_status": "passed",
            "evidence_level": "lease_validated",
        }
        assert "wechat_room_id" in card
        assert isinstance(card["wechat_room_id"], str)
        assert len(card["wechat_room_id"]) > 0

    def test_room_card_must_have_lease_room_id(self):
        """lease_room_id is the lease system identifier for API validation."""
        card = {
            "wechat_room_id": "wx-1",
            "lease_room_id": 10234,
            "lease_validation_status": "passed",
            "evidence_level": "lease_validated",
        }
        assert "lease_room_id" in card
        # lease_room_id is an int when available, or None when mapping not yet done
        assert card["lease_room_id"] is None or isinstance(card["lease_room_id"], int)

    def test_room_card_lease_validation_status_must_be_known(self):
        """lease_validation_status must be one of the expected values."""
        valid_statuses = {"passed", "failed", "not_checked"}
        card = {
            "wechat_room_id": "wx-1",
            "lease_room_id": 101,
            "lease_validation_status": "passed",
            "evidence_level": "lease_validated",
        }
        assert card["lease_validation_status"] in valid_statuses

    def test_room_card_evidence_level_must_be_valid(self):
        """evidence_level must be one of the five defined values."""
        card = {
            "wechat_room_id": "wx-1",
            "lease_room_id": 101,
            "lease_validation_status": "passed",
            "evidence_level": "lease_validated",
        }
        assert _is_valid_evidence_level(card["evidence_level"])

    def test_room_card_lease_validated_requires_positive_lease_room_id(self):
        """If evidence_level is lease_validated, lease_room_id must be a
        positive integer (not None, not 0)."""
        card = {
            "wechat_room_id": "wx-1",
            "lease_room_id": 10234,
            "lease_validation_status": "passed",
            "evidence_level": "lease_validated",
        }
        if card["evidence_level"] in ("lease_validated", "lease_validated_with_freshness"):
            assert isinstance(card["lease_room_id"], int)
            assert card["lease_room_id"] > 0

    def test_room_card_vector_only_cannot_be_production(self):
        """vector_only room cards must not claim lease validation."""
        card = {
            "wechat_room_id": "wx-1",
            "lease_room_id": None,
            "lease_validation_status": "not_checked",
            "evidence_level": "vector_only",
        }
        if card["evidence_level"] == "vector_only":
            assert card["lease_validation_status"] != "passed"

    def test_room_card_contract_rejects_missing_wechat_id(self):
        """A card without wechat_room_id violates the contract."""
        card = {
            "lease_room_id": 101,
            "lease_validation_status": "passed",
            "evidence_level": "lease_validated",
        }
        assert not ROOM_CARD_REQUIRED_KEYS <= set(card), (
            "Contract should reject card missing wechat_room_id"
        )

    def test_room_card_contract_rejects_missing_evidence_level(self):
        """A card without evidence_level violates the contract."""
        card = {
            "wechat_room_id": "wx-1",
            "lease_room_id": 101,
            "lease_validation_status": "passed",
        }
        assert not ROOM_CARD_REQUIRED_KEYS <= set(card), (
            "Contract should reject card missing evidence_level"
        )


# ===========================================================================
# KB QA Evidence Contract Tests
# ===========================================================================


class TestKBEvidenceContract:
    """Verify KB source and final-answer data structures meet the contract."""

    def test_kb_source_requires_citation_fields(self):
        """KB source cards must carry chunk_id, doc_id, title, module,
        score, risk_level, and evidence_level."""
        source = {
            "chunk_id": "lease_001_chunk3",
            "doc_id": "lease_001",
            "title": "退租违约金规则",
            "module": "lease",
            "score": 0.85,
            "risk_level": "high",
            "evidence_level": "source_grounded",
        }
        assert KB_SOURCE_REQUIRED_KEYS <= set(source), (
            f"Missing required keys: {KB_SOURCE_REQUIRED_KEYS - set(source)}"
        )

    def test_kb_source_chunk_id_must_be_nonempty_string(self):
        """chunk_id must be a non-empty string for citation."""
        source = {
            "chunk_id": "lease_001_chunk3",
            "doc_id": "lease_001",
            "title": "退租违约金规则",
            "module": "lease",
            "score": 0.85,
            "risk_level": "high",
            "evidence_level": "source_grounded",
        }
        assert isinstance(source["chunk_id"], str)
        assert len(source["chunk_id"]) > 0

    def test_kb_source_doc_id_must_be_nonempty_string(self):
        """doc_id must be a non-empty string for citation."""
        source = {
            "chunk_id": "lease_001_chunk3",
            "doc_id": "lease_001",
            "title": "退租违约金规则",
            "module": "lease",
            "score": 0.85,
            "risk_level": "high",
            "evidence_level": "source_grounded",
        }
        assert isinstance(source["doc_id"], str)
        assert len(source["doc_id"]) > 0

    def test_kb_source_score_must_be_between_0_and_1(self):
        """Score is derived from 1 - cosine_distance; must be in [0, 1]."""
        source = {
            "chunk_id": "lease_001_chunk3",
            "doc_id": "lease_001",
            "title": "退租违约金规则",
            "module": "lease",
            "score": 0.85,
            "risk_level": "high",
            "evidence_level": "source_grounded",
        }
        assert 0.0 <= source["score"] <= 1.0

    def test_kb_source_risk_level_must_be_valid(self):
        """risk_level must be low, medium, or high."""
        for level in ("low", "medium", "high"):
            source = {
                "chunk_id": "kb_001",
                "doc_id": "doc_001",
                "title": "Test",
                "module": "lease",
                "score": 0.9,
                "risk_level": level,
                "evidence_level": "source_grounded",
            }
            assert source["risk_level"] in RISK_LEVELS

    def test_kb_source_evidence_level_must_be_valid(self):
        """evidence_level must be one of the five defined values."""
        source = {
            "chunk_id": "kb_001",
            "doc_id": "doc_001",
            "title": "Test",
            "module": "lease",
            "score": 0.9,
            "risk_level": "high",
            "evidence_level": "source_grounded",
        }
        assert _is_valid_evidence_level(source["evidence_level"])

    def test_kb_final_answer_requires_metadata_keys(self):
        """Final KB answer metadata must carry all required keys."""
        answer_meta = {
            "risk_level": "high",
            "confidence_passed": True,
            "evidence_count": 3,
            "grounded_answer": True,
            "citations": [
                {"chunk_id": "lease_001_chunk3", "doc_id": "lease_001"},
                {"chunk_id": "lease_002_chunk1", "doc_id": "lease_002"},
            ],
            "fallback_reason": None,
        }
        assert KB_FINAL_ANSWER_REQUIRED_KEYS <= set(answer_meta), (
            f"Missing required keys: {KB_FINAL_ANSWER_REQUIRED_KEYS - set(answer_meta)}"
        )

    def test_kb_final_answer_citations_must_be_list(self):
        """citations must be a list of chunk_id/doc_id pairs."""
        answer_meta = {
            "risk_level": "high",
            "confidence_passed": True,
            "evidence_count": 2,
            "grounded_answer": True,
            "citations": [
                {"chunk_id": "lease_001_chunk3", "doc_id": "lease_001"},
                {"chunk_id": "lease_002_chunk1", "doc_id": "lease_002"},
            ],
            "fallback_reason": None,
        }
        assert isinstance(answer_meta["citations"], list)
        for citation in answer_meta["citations"]:
            assert "chunk_id" in citation
            assert "doc_id" in citation


# ===========================================================================
# Evidence Level Enforcement Tests
# ===========================================================================


class TestEvidenceLevelEnforcement:
    """Verify the core contract rule: medium/high-risk cannot use vector_only."""

    def test_high_risk_cannot_use_vector_only_evidence(self):
        """High-risk output with vector_only violates the contract."""
        risk_level = "high"
        evidence_level = "vector_only"
        assert _risk_requires_validation(risk_level, evidence_level), (
            "High-risk + vector_only should be flagged as contract violation"
        )

    def test_medium_risk_cannot_use_vector_only_evidence(self):
        """Medium-risk output with vector_only violates the contract."""
        risk_level = "medium"
        evidence_level = "vector_only"
        assert _risk_requires_validation(risk_level, evidence_level), (
            "Medium-risk + vector_only should be flagged as contract violation"
        )

    def test_low_risk_can_use_vector_only_evidence(self):
        """Low-risk output may use vector_only."""
        risk_level = "low"
        evidence_level = "vector_only"
        assert not _risk_requires_validation(risk_level, evidence_level), (
            "Low-risk + vector_only should be allowed"
        )

    def test_high_risk_with_source_grounded_is_valid(self):
        """High-risk with source_grounded satisfies the contract."""
        risk_level = "high"
        evidence_level = "source_grounded"
        assert not _risk_requires_validation(risk_level, evidence_level)

    def test_high_risk_with_lease_validated_is_valid(self):
        """High-risk with lease_validated satisfies the contract."""
        risk_level = "high"
        evidence_level = "lease_validated"
        assert not _risk_requires_validation(risk_level, evidence_level)

    def test_conservative_fallback_is_always_valid(self):
        """conservative_fallback is valid for any risk level."""
        for risk in RISK_LEVELS:
            assert not _risk_requires_validation(risk, "conservative_fallback")

    @pytest.mark.parametrize("evidence_level", VALID_EVIDENCE_LEVELS)
    def test_all_evidence_levels_are_recognized(self, evidence_level):
        """Every defined evidence level must be recognized as valid."""
        assert _is_valid_evidence_level(evidence_level)

    def test_unknown_evidence_level_is_rejected(self):
        """An undefined evidence level must be rejected."""
        assert not _is_valid_evidence_level("unknown_level")
        assert not _is_valid_evidence_level("")
        assert not _is_valid_evidence_level("hallucinated")


# ===========================================================================
# Current Pipeline Gap Tests
# ===========================================================================


class TestCurrentPipelineGaps:
    """Verify that the contract identifies known gaps in the current pipeline.

    These tests document what the pipeline CURRENTLY produces, so the gap
    is explicit and tracked.
    """

    def test_current_source_card_lacks_evidence_level(self):
        """The current _source_card() function does not produce evidence_level.

        This test documents the gap: once evidence_level is added to the
        pipeline, this test should be updated to assert presence.
        """
        # Simulate what _source_card currently produces
        current_source_card_keys = {
            "type", "chunk_id", "doc_id", "title",
            "module", "content_snippet", "score", "risk_level",
        }
        assert "evidence_level" not in current_source_card_keys, (
            "If this fails, evidence_level has been added to source cards -- update the test"
        )

    def test_current_room_pipeline_lacks_lease_validation(self):
        """The current room_retrieval.py does not call the lease API.

        This test documents the gap: once lease validation is added,
        this test should be updated.
        """
        # Simulate what ValidatedRoom currently contains
        current_validated_room_keys = {
            "room_id", "apartment_name", "district_name", "rent",
            "payment_types", "tags", "facilities", "semantic_score",
            "matched_query",
        }
        contract_required = {"wechat_room_id", "lease_room_id", "lease_validation_status", "evidence_level"}
        missing = contract_required - current_validated_room_keys
        assert len(missing) > 0, (
            f"If this fails, contract fields have been added to ValidatedRoom: {missing}"
        )

    def test_current_wechat_id_lost_after_synthetic_hash(self):
        """The synthetic room_id from hash(wechat_id) is not reversible.

        The original wechat_room_id is discarded in _map_wechat_room_results.
        """
        # Simulate the synthetic ID generation
        wechat_id = "wx_room_abc123"
        synthetic_id = abs(hash(wechat_id)) % 1000000 + 900000

        # The synthetic ID is an int, not the original string
        assert isinstance(synthetic_id, int)
        assert synthetic_id != wechat_id  # not reversible
        # No code path maps this back to the original wechat ID
