"""Tests for room retrieval — verifies logic without hitting Milvus."""

from aptguide2.rag.room_retrieval import (
    _build_filters,
    _parse_json_field,
    enrich_candidates_from_vector,
)
from aptguide2.rag.schemas import QueryUnderstandingResult, RoomCandidate


def _make_query_result(task="room_search", **kwargs):
    return QueryUnderstandingResult(
        raw_message="test",
        task=task,
        **kwargs,
    )


class TestBuildFilters:
    def test_empty_filters(self):
        qr = _make_query_result()
        assert _build_filters(qr) == {}

    def test_district_filter(self):
        qr = _make_query_result(hard_filters={"district_id": 1001})
        assert _build_filters(qr) == {"district_id": 1001}

    def test_budget_filter(self):
        qr = _make_query_result(hard_filters={"max_rent": 2000})
        assert _build_filters(qr) == {"max_rent": 2000}

    def test_combined_filters(self):
        qr = _make_query_result(hard_filters={"district_id": 1005, "max_rent": 1500})
        f = _build_filters(qr)
        assert f["district_id"] == 1005
        assert f["max_rent"] == 1500

    def test_none_values_skipped(self):
        qr = _make_query_result(hard_filters={"district_id": None, "max_rent": 2000})
        assert _build_filters(qr) == {"max_rent": 2000}


class TestParseJsonField:
    def test_list_passthrough(self):
        assert _parse_json_field(["a", "b"]) == ["a", "b"]

    def test_valid_json_string(self):
        assert _parse_json_field('["x", "y"]') == ["x", "y"]

    def test_invalid_json_string(self):
        assert _parse_json_field("not json") == []

    def test_empty_string(self):
        assert _parse_json_field("") == []

    def test_none(self):
        assert _parse_json_field(None) == []

    def test_integer(self):
        assert _parse_json_field(42) == []


class TestEnrichCandidates:
    def test_empty_candidates(self):
        assert enrich_candidates_from_vector([], None) == []

    def test_enrichment_with_mock_adapter(self):
        """Test that enrichment merges candidate and vector data."""
        candidates = [
            RoomCandidate(room_id=1001, apartment_id=500, semantic_score=0.9, matched_query="番禺"),
            RoomCandidate(room_id=1002, apartment_id=501, semantic_score=0.8, matched_query="天河"),
        ]

        class MockAdapter:
            def get_room_by_ids(self, room_ids):
                return [
                    {"room_id": 1001, "apartment_id": 500, "district_id": 1005, "district_name": "番禺区",
                     "rent": 1500, "payment_types": '["月付"]', "lease_terms": '[6, 12]',
                     "tags": '["近地铁"]', "facilities": '["空调"]'},
                    {"room_id": 1002, "apartment_id": 501, "district_id": 1001, "district_name": "天河区",
                     "rent": 2500, "payment_types": '["季付"]', "lease_terms": '[12]',
                     "tags": '["独卫"]', "facilities": '["洗衣机"]'},
                ]

        enriched = enrich_candidates_from_vector(candidates, MockAdapter())
        assert len(enriched) == 2
        assert enriched[0]["room_id"] == 1001
        assert enriched[0]["rent"] == 1500
        assert enriched[0]["tags"] == ["近地铁"]
        assert enriched[0]["semantic_score"] == 0.9
        assert enriched[1]["district_name"] == "天河区"
