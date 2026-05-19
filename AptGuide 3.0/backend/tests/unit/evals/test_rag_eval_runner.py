"""Unit tests for the RAG evaluation runner.

Tests cover:
  - Task 1: Schema validation (validate_eval_case)
  - Task 2: Room criteria strengthening (_check_criteria)
  - Task 3: KB criteria strengthening (citations_match_source_cards)
  - Task 5: Failure owner classification (classify_failure_owner)
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

# ---------------------------------------------------------------------------
# Import path setup -- the eval runner lives outside src/aptguide3
# ---------------------------------------------------------------------------

_EVALS_RUNNERS = str(Path(__file__).resolve().parents[3] / "evals" / "runners")
if _EVALS_RUNNERS not in sys.path:
    sys.path.insert(0, _EVALS_RUNNERS)

from run_rag_eval import (  # noqa: E402
    VALID_LEASE_EVIDENCE_LEVELS,
    _check_criteria,
    _check_entity_resolution_criteria,
    citations_match_source_cards,
    classify_failure_owner,
    validate_eval_case,
)

# ===========================================================================
# Task 1: Schema Validation
# ===========================================================================


class TestValidateEvalCase:
    """validate_eval_case rejects cases missing required fields."""

    def test_high_risk_kb_case_allows_empty_expected_doc_ids(self):
        """A high-risk kb_qa case without expected_doc_ids is now allowed
        (will be populated after first live discovery run)."""
        case = {
            "id": "kb-risk-1",
            "task": "kb_qa",
            "query": "押金不退怎么办",
            "risk_level": "high",
        }
        errors = validate_eval_case(case)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_valid_high_risk_kb_case_passes(self):
        case = {
            "id": "kb-risk-1",
            "task": "kb_qa",
            "query": "押金不退怎么办",
            "risk_level": "high",
            "expected_doc_ids": ["KB-LS-011"],
        }
        errors = validate_eval_case(case)
        assert errors == []

    def test_missing_id_rejected(self):
        case = {"task": "kb_qa", "query": "test"}
        errors = validate_eval_case(case)
        assert any("'id'" in e for e in errors)

    def test_missing_task_allowed(self):
        """Missing task is now allowed for T2/T3 cases that use expected_route."""
        case = {"id": "x", "query": "test"}
        errors = validate_eval_case(case)
        assert errors == []

    def test_missing_query_rejected(self):
        case = {"id": "x", "task": "kb_qa"}
        errors = validate_eval_case(case)
        assert any("'query'" in e for e in errors)

    def test_room_search_requires_must_validate_with_lease(self):
        case = {
            "id": "room-1",
            "task": "room_search",
            "query": "找房",
        }
        errors = validate_eval_case(case)
        assert any("must_validate_with_lease" in e for e in errors)

    def test_room_search_with_lease_expectation_passes(self):
        case = {
            "id": "room-1",
            "task": "room_search",
            "query": "找房",
            "expected": {"must_validate_with_lease": True},
        }
        errors = validate_eval_case(case)
        assert errors == []

    def test_low_risk_kb_does_not_require_expected_doc_ids(self):
        case = {
            "id": "kb-low-1",
            "task": "kb_qa",
            "query": "设施坏了谁修",
            "risk_level": "low",
        }
        errors = validate_eval_case(case)
        # No error about expected_doc_ids
        assert not any("expected_doc_ids" in e for e in errors)


# ===========================================================================
# Task 2: Room Criteria Strengthening
# ===========================================================================


class TestRoomCriteriaStrengthening:
    """_check_criteria must_validate_with_lease checks card metadata."""

    def _make_response(self, cards, metadata=None):
        return SimpleNamespace(
            cards=cards,
            metadata=metadata or {},
            message="",
            phase="room_search",
        )

    def test_room_validation_criteria_rejects_vector_only_card(self):
        """A card with evidence_level=vector_only must fail lease validation."""
        response = self._make_response(
            cards=[{
                "type": "room_card",
                "room_id": 1,
                "evidence_level": "vector_only",
                "lease_validation_status": "not_checked",
                "lease_room_id": None,
            }],
        )
        case = {"expected": {"must_validate_with_lease": True}}
        result = _check_criteria(response, case)
        assert result["must_validate_with_lease"]["pass"] is False

    def test_lease_validated_card_passes(self):
        response = self._make_response(
            cards=[{
                "type": "room_card",
                "room_id": 101,
                "evidence_level": "lease_validated",
                "lease_validation_status": "passed",
                "lease_room_id": 101,
            }],
        )
        case = {"expected": {"must_validate_with_lease": True}}
        result = _check_criteria(response, case)
        assert result["must_validate_with_lease"]["pass"] is True

    def test_mapped_verified_card_passes(self):
        response = self._make_response(
            cards=[{
                "type": "room_card",
                "room_id": 200,
                "evidence_level": "mapped_verified",
                "lease_validation_status": "passed",
                "lease_room_id": 200,
            }],
        )
        case = {"expected": {"must_validate_with_lease": True}}
        result = _check_criteria(response, case)
        assert result["must_validate_with_lease"]["pass"] is True

    def test_missing_lease_validation_status_fails(self):
        response = self._make_response(
            cards=[{
                "type": "room_card",
                "room_id": 1,
                "evidence_level": "lease_validated",
                "lease_room_id": 1,
                # lease_validation_status missing
            }],
        )
        case = {"expected": {"must_validate_with_lease": True}}
        result = _check_criteria(response, case)
        assert result["must_validate_with_lease"]["pass"] is False

    def test_mixed_valid_and_invalid_cards_fails(self):
        response = self._make_response(
            cards=[
                {
                    "type": "room_card",
                    "room_id": 101,
                    "evidence_level": "lease_validated",
                    "lease_validation_status": "passed",
                    "lease_room_id": 101,
                },
                {
                    "type": "room_card",
                    "room_id": 2,
                    "evidence_level": "vector_only",
                    "lease_validation_status": "not_checked",
                    "lease_room_id": None,
                },
            ],
        )
        case = {"expected": {"must_validate_with_lease": True}}
        result = _check_criteria(response, case)
        assert result["must_validate_with_lease"]["pass"] is False

    def test_no_room_cards_passes(self):
        """When no room cards returned, validation passes (no violation)."""
        response = self._make_response(cards=[])
        case = {"expected": {"must_validate_with_lease": True}}
        result = _check_criteria(response, case)
        assert result["must_validate_with_lease"]["pass"] is True


# ===========================================================================
# Task 3: KB Criteria / Citation Validation
# ===========================================================================


class TestCitationValidation:
    """citations_match_source_cards validates citations against source cards."""

    def test_citations_must_match_source_cards(self):
        cards = [
            {"type": "kb_source", "doc_id": "KB-LS-011", "chunk_id": "KB-LS-011"},
        ]
        citations = [
            {"doc_id": "KB-LS-011", "chunk_id": "KB-LS-011"},
        ]
        assert citations_match_source_cards(citations, cards) is True

    def test_citation_not_in_source_cards_fails(self):
        cards = [
            {"type": "kb_source", "doc_id": "KB-LS-011", "chunk_id": "KB-LS-011"},
        ]
        citations = [
            {"doc_id": "KB-FAKE-999", "chunk_id": "KB-FAKE-999"},
        ]
        assert citations_match_source_cards(citations, cards) is False

    def test_empty_citations_fails(self):
        cards = [
            {"type": "kb_source", "doc_id": "KB-LS-011", "chunk_id": "KB-LS-011"},
        ]
        assert citations_match_source_cards([], cards) is False

    def test_empty_source_cards_with_citation_fails(self):
        citations = [{"doc_id": "KB-LS-011", "chunk_id": "KB-LS-011"}]
        assert citations_match_source_cards(citations, []) is False

    def test_multiple_citations_all_match(self):
        cards = [
            {"type": "kb_source", "doc_id": "A", "chunk_id": "1"},
            {"type": "kb_source", "doc_id": "B", "chunk_id": "2"},
        ]
        citations = [
            {"doc_id": "A", "chunk_id": "1"},
            {"doc_id": "B", "chunk_id": "2"},
        ]
        assert citations_match_source_cards(citations, cards) is True

    def test_partial_citation_mismatch_fails(self):
        cards = [
            {"type": "kb_source", "doc_id": "A", "chunk_id": "1"},
        ]
        citations = [
            {"doc_id": "A", "chunk_id": "1"},
            {"doc_id": "B", "chunk_id": "2"},  # not in source cards
        ]
        assert citations_match_source_cards(citations, cards) is False


# ===========================================================================
# Task 3: KB Criteria Checks
# ===========================================================================


class TestKBCriteria:
    """_check_criteria KB criteria: citations, grounded, source cards."""

    def _make_response(self, cards, metadata=None):
        return SimpleNamespace(
            cards=cards,
            metadata=metadata or {},
            message="test answer",
            phase="kb_qa",
        )

    def test_must_have_citations_for_high_risk_passes_with_citations(self):
        response = self._make_response(
            cards=[{"type": "kb_source", "doc_id": "KB-1", "chunk_id": "C1"}],
            metadata={"citations": [{"doc_id": "KB-1", "chunk_id": "C1"}]},
        )
        case = {"expected": {"must_have_citations_for_high_risk": True}}
        result = _check_criteria(response, case)
        assert result["must_have_citations_for_high_risk"]["pass"] is True

    def test_must_have_citations_for_high_risk_fails_without_citations(self):
        response = self._make_response(
            cards=[{"type": "kb_source", "doc_id": "KB-1", "chunk_id": "C1"}],
            metadata={"citations": []},
        )
        case = {"expected": {"must_have_citations_for_high_risk": True}}
        result = _check_criteria(response, case)
        assert result["must_have_citations_for_high_risk"]["pass"] is False

    def test_must_have_grounded_answer_passes(self):
        response = self._make_response(
            cards=[],
            metadata={"grounded_answer": True},
        )
        case = {"expected": {"must_have_grounded_answer": True}}
        result = _check_criteria(response, case)
        assert result["must_have_grounded_answer"]["pass"] is True

    def test_must_have_grounded_answer_fails_when_not_grounded(self):
        response = self._make_response(
            cards=[],
            metadata={"grounded_answer": False, "confidence_passed": True},
        )
        case = {"expected": {"must_have_grounded_answer": True}}
        result = _check_criteria(response, case)
        assert result["must_have_grounded_answer"]["pass"] is False

    def test_must_have_grounded_answer_passes_when_confidence_blocked(self):
        """If confidence gate blocked, fallback is acceptable."""
        response = self._make_response(
            cards=[],
            metadata={"grounded_answer": False, "confidence_passed": False},
        )
        case = {"expected": {"must_have_grounded_answer": True}}
        result = _check_criteria(response, case)
        assert result["must_have_grounded_answer"]["pass"] is True

    def test_must_have_source_cards_passes_with_sources(self):
        response = self._make_response(
            cards=[{"type": "kb_source", "doc_id": "KB-1", "chunk_id": "C1"}],
            metadata={},
        )
        case = {"expected": {"must_have_source_cards": True}}
        result = _check_criteria(response, case)
        assert result["must_have_source_cards"]["pass"] is True

    def test_must_have_source_cards_fails_without_sources(self):
        response = self._make_response(
            cards=[],
            metadata={"confidence_passed": True},
        )
        case = {"expected": {"must_have_source_cards": True}}
        result = _check_criteria(response, case)
        assert result["must_have_source_cards"]["pass"] is False


# ===========================================================================
# Task 5: Failure Owner Classification
# ===========================================================================


class TestFailureOwnerClassification:
    """classify_failure_owner returns exactly one canonical owner."""

    def test_failure_owner_is_single_value(self):
        result = classify_failure_owner({"rec_diagnostic": {"failure_stage": "lease_validation_empty"}})
        assert result == "lease_validation"

    def test_error_with_connect_returns_data_alignment(self):
        result = classify_failure_owner({
            "status": "ERROR",
            "error": "Connection refused to lease API",
        })
        assert result == "data_alignment"

    def test_error_without_connect_returns_runtime_error(self):
        result = classify_failure_owner({
            "status": "ERROR",
            "error": "KeyError: 'room_id'",
        })
        assert result == "runtime_error"

    def test_clarify_phase_returns_understanding(self):
        result = classify_failure_owner({"phase": "clarify"})
        assert result == "understanding"

    def test_validator_reason_returns_understanding(self):
        result = classify_failure_owner({
            "understanding_diagnostic": {"validator_reason": "low confidence"},
        })
        assert result == "understanding"

    def test_vector_recall_empty_returns_vector_recall(self):
        result = classify_failure_owner({
            "rec_diagnostic": {"failure_stage": "vector_recall_empty"},
        })
        assert result == "vector_recall"

    def test_ranking_empty_returns_ranking(self):
        result = classify_failure_owner({
            "rec_diagnostic": {"failure_stage": "ranking_empty"},
        })
        assert result == "ranking"

    def test_confidence_gate_returns_confidence_gate(self):
        result = classify_failure_owner({
            "rec_diagnostic": {"confidence_passed": False},
        })
        assert result == "confidence_gate"

    def test_identity_mapping_for_synthetic_ids(self):
        result = classify_failure_owner({
            "task": "room_search",
            "rec_diagnostic": {
                "source_record_ids": ["syn_001", "syn_002"],
                "mapped_verified_count": 0,
            },
        })
        assert result == "identity_mapping"

    def test_fail_without_expected_returns_dataset_gap(self):
        result = classify_failure_owner({
            "status": "FAIL",
            "criteria": {"must_cite_source": {"pass": False}},
            "expected_doc_ids": [],
        })
        assert result == "dataset_gap"

    def test_fail_with_expected_returns_vector_recall(self):
        result = classify_failure_owner({
            "status": "FAIL",
            "criteria": {"must_cite_source": {"pass": False}},
            "expected_doc_ids": ["KB-001"],
        })
        assert result == "vector_recall"

    def test_grounded_answer_failure(self):
        result = classify_failure_owner({
            "task": "kb_qa",
            "criteria": {
                "must_have_grounded_answer": {"pass": False},
            },
        })
        assert result == "grounded_answer"

    def test_canonical_owners_are_all_strings(self):
        """Every classification returns a string, never None or list."""
        cases = [
            {"status": "ERROR", "error": "timeout"},
            {"status": "ERROR", "error": "KeyError"},
            {"phase": "clarify"},
            {"rec_diagnostic": {"failure_stage": "vector_recall_empty"}},
            {"rec_diagnostic": {"failure_stage": "lease_validation_empty"}},
            {"rec_diagnostic": {"failure_stage": "ranking_empty"}},
            {"rec_diagnostic": {"confidence_passed": False}},
            {"task": "room_search", "rec_diagnostic": {"source_record_ids": ["x"], "mapped_verified_count": 0}},
            {"status": "FAIL", "criteria": {"x": {"pass": False}}, "expected_doc_ids": []},
            {"task": "kb_qa", "criteria": {"must_have_grounded_answer": {"pass": False}}},
        ]
        for case in cases:
            result = classify_failure_owner(case)
            assert isinstance(result, str), f"Expected string, got {type(result)} for {case}"
            assert len(result) > 0, f"Empty owner for {case}"


# ===========================================================================
# VALID_LEASE_EVIDENCE_LEVELS constant
# ===========================================================================


class TestLeaseEvidenceLevels:
    """Verify the canonical set of lease-validated evidence levels."""

    def test_mapped_verified_included(self):
        assert "mapped_verified" in VALID_LEASE_EVIDENCE_LEVELS

    def test_vector_only_excluded(self):
        assert "vector_only" not in VALID_LEASE_EVIDENCE_LEVELS

    def test_lease_validated_included(self):
        assert "lease_validated" in VALID_LEASE_EVIDENCE_LEVELS

    def test_lease_validated_with_freshness_included(self):
        assert "lease_validated_with_freshness" in VALID_LEASE_EVIDENCE_LEVELS


# ===========================================================================
# Room Search Criteria Tests
# ===========================================================================


class TestRoomSearchCriteria:
    """_check_criteria room search criteria: response_not_empty, district_match,
    price_in_range, amenity_match, latency_ok."""

    def _make_response(self, cards, metadata=None):
        return SimpleNamespace(
            cards=cards,
            metadata=metadata or {},
            message="",
            phase="room_search",
        )

    def test_response_not_empty_passes_with_cards(self):
        response = self._make_response(cards=[{"type": "room_card", "room_id": 1}])
        case = {"expected": {"response_not_empty": True}}
        result = _check_criteria(response, case)
        assert result["response_not_empty"]["pass"] is True

    def test_response_not_empty_fails_without_cards(self):
        response = self._make_response(cards=[])
        case = {"expected": {"response_not_empty": True}}
        result = _check_criteria(response, case)
        assert result["response_not_empty"]["pass"] is False

    def test_district_match_passes(self):
        response = self._make_response(
            cards=[{"type": "room_card", "room_id": 1, "district_name": "天河区"}]
        )
        case = {"expected": {"district_match": True}, "expected_district": "天河区"}
        result = _check_criteria(response, case)
        assert result["district_match"]["pass"] is True

    def test_district_match_fails(self):
        response = self._make_response(
            cards=[{"type": "room_card", "room_id": 1, "district_name": "番禺区"}]
        )
        case = {"expected": {"district_match": True}, "expected_district": "天河区"}
        result = _check_criteria(response, case)
        assert result["district_match"]["pass"] is False

    def test_district_match_passes_no_room_cards(self):
        response = self._make_response(cards=[{"type": "kb_source"}])
        case = {"expected": {"district_match": True}, "expected_district": "天河区"}
        result = _check_criteria(response, case)
        assert result["district_match"]["pass"] is True

    def test_price_in_range_passes(self):
        response = self._make_response(
            cards=[{"type": "room_card", "room_id": 1, "rent": 1500}]
        )
        case = {"expected": {"price_in_range": True}, "expected_price_max": 2000}
        result = _check_criteria(response, case)
        assert result["price_in_range"]["pass"] is True

    def test_price_in_range_fails(self):
        response = self._make_response(
            cards=[{"type": "room_card", "room_id": 1, "rent": 2500}]
        )
        case = {"expected": {"price_in_range": True}, "expected_price_max": 2000}
        result = _check_criteria(response, case)
        assert result["price_in_range"]["pass"] is False

    def test_amenity_match_passes(self):
        response = self._make_response(
            cards=[{"type": "room_card", "room_id": 1, "facilities": "空调 洗衣机", "tags": ""}]
        )
        case = {"expected": {"amenity_match": True}, "expected_amenities": ["空调"]}
        result = _check_criteria(response, case)
        assert result["amenity_match"]["pass"] is True

    def test_amenity_match_fails(self):
        response = self._make_response(
            cards=[{"type": "room_card", "room_id": 1, "facilities": "洗衣机", "tags": ""}]
        )
        case = {"expected": {"amenity_match": True}, "expected_amenities": ["空调"]}
        result = _check_criteria(response, case)
        assert result["amenity_match"]["pass"] is False

    def test_latency_ok_passes(self):
        response = self._make_response(cards=[])
        case = {"expected": {"latency_ok": True, "latency_max_ms": 15000}, "_latency_ms": 5000}
        result = _check_criteria(response, case)
        assert result["latency_ok"]["pass"] is True

    def test_latency_ok_fails(self):
        response = self._make_response(cards=[])
        case = {"expected": {"latency_ok": True, "latency_max_ms": 15000}, "_latency_ms": 20000}
        result = _check_criteria(response, case)
        assert result["latency_ok"]["pass"] is False

    def test_latency_ok_skipped_when_no_latency(self):
        response = self._make_response(cards=[])
        case = {"expected": {"latency_ok": True}}
        result = _check_criteria(response, case)
        assert "latency_ok" not in result


# ===========================================================================
# Entity Resolution Criteria Tests
# ===========================================================================


class TestEntityResolutionCriteria:
    """_check_entity_resolution_criteria verifies resolved entities."""

    def _make_response(self, phase="rag"):
        return SimpleNamespace(cards=[], metadata={}, message="", phase=phase)

    def test_resolved_district_passes(self):
        response = self._make_response()
        case = {"expected": {"expected_resolved_district": "天河区"}}
        diagnostic = {"parsed_entities": {"district": "天河区"}}
        result = _check_entity_resolution_criteria(response, case, diagnostic)
        assert result["resolved_district"]["pass"] is True

    def test_resolved_district_fails(self):
        response = self._make_response()
        case = {"expected": {"expected_resolved_district": "天河区"}}
        diagnostic = {"parsed_entities": {"district": "番禺区"}}
        result = _check_entity_resolution_criteria(response, case, diagnostic)
        assert result["resolved_district"]["pass"] is False

    def test_resolved_room_type_passes(self):
        response = self._make_response()
        case = {"expected": {"expected_resolved_room_type": "单间"}}
        diagnostic = {"parsed_entities": {"room_type": "单间"}}
        result = _check_entity_resolution_criteria(response, case, diagnostic)
        assert result["resolved_room_type"]["pass"] is True

    def test_resolved_payment_type_passes(self):
        response = self._make_response()
        case = {"expected": {"expected_resolved_payment_type": "月付"}}
        diagnostic = {"parsed_entities": {"payment_type": "月付"}}
        result = _check_entity_resolution_criteria(response, case, diagnostic)
        assert result["resolved_payment_type"]["pass"] is True

    def test_no_expected_entities_returns_empty(self):
        response = self._make_response()
        case = {"expected": {"some_other_field": True}}
        diagnostic = {}
        result = _check_entity_resolution_criteria(response, case, diagnostic)
        assert result == {}

    def test_non_dict_expected_returns_empty(self):
        response = self._make_response()
        case = {"expected": "free text"}
        diagnostic = {}
        result = _check_entity_resolution_criteria(response, case, diagnostic)
        assert result == {}


# ===========================================================================
# Failure Owner Classification (updated for criteria-based room search)
# ===========================================================================


class TestFailureOwnerUpdated:
    """Test failure owner classification with updated data format."""

    def test_fail_without_expected_returns_dataset_gap(self):
        result = classify_failure_owner({
            "status": "FAIL",
            "criteria": {"must_cite_source": {"pass": False}},
            "expected_doc_ids": [],
        })
        assert result == "dataset_gap"

    def test_fail_with_expected_returns_vector_recall(self):
        result = classify_failure_owner({
            "status": "FAIL",
            "criteria": {"must_cite_source": {"pass": False}},
            "expected_doc_ids": ["KB-001"],
        })
        assert result == "vector_recall"
