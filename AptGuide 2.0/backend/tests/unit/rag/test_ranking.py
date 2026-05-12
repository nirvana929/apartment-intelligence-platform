"""Tests for room ranking — verifies scoring logic without external deps."""

from aptguide2.rag.ranking import (
    _score_area,
    _score_budget,
    _score_tags,
    rank_rooms,
)
from aptguide2.rag.schemas import QueryUnderstandingResult


def _make_query_result(**kwargs):
    defaults = {"raw_message": "test", "task": "room_search"}
    defaults.update(kwargs)
    return QueryUnderstandingResult(**defaults)


class TestScoreBudget:
    def test_no_budget(self):
        assert _score_budget(1500, None) == 0.5

    def test_zero_rent(self):
        assert _score_budget(0, 2000) == 0.5

    def test_well_under(self):
        assert _score_budget(1000, 2000) == 1.0

    def test_good_value(self):
        assert _score_budget(1700, 2000) == 0.85

    def test_within_budget(self):
        assert _score_budget(1950, 2000) == 0.65

    def test_slightly_over(self):
        assert _score_budget(2100, 2000) == 0.3

    def test_way_over(self):
        assert _score_budget(3000, 2000) == 0.0


class TestScoreArea:
    def test_no_target(self):
        assert _score_area(1001, None) == 0.5

    def test_match(self):
        assert _score_area(1005, 1005) == 1.0

    def test_mismatch(self):
        assert _score_area(1001, 1005) == 0.0


class TestScoreTags:
    def test_no_preferences(self):
        assert _score_tags({"tags": ["近地铁"]}, []) == 0.5

    def test_full_match(self):
        room = {"tags": ["近地铁", "独卫"], "facilities": ["空调"]}
        assert _score_tags(room, ["近地铁", "独卫"]) == 1.0

    def test_partial_match(self):
        room = {"tags": ["近地铁"], "facilities": []}
        assert _score_tags(room, ["近地铁", "独卫"]) == 0.5

    def test_no_match(self):
        room = {"tags": ["近地铁"], "facilities": []}
        assert _score_tags(room, ["独卫", "朝南"]) == 0.0

    def test_facilities_count(self):
        room = {"tags": [], "facilities": ["空调", "洗衣机"]}
        assert _score_tags(room, ["空调"]) == 1.0


class TestRankRooms:
    def test_empty_candidates(self):
        qr = _make_query_result()
        assert rank_rooms([], qr) == []

    def test_ranking_order(self):
        """Better budget + area match should rank higher."""
        qr = _make_query_result(
            hard_filters={"max_rent": 2000, "district_id": 1005},
            soft_preferences=["近地铁"],
        )
        candidates = [
            {"room_id": 1, "rent": 2500, "district_id": 1001, "semantic_score": 0.9,
             "tags": [], "facilities": []},
            {"room_id": 2, "rent": 1500, "district_id": 1005, "semantic_score": 0.7,
             "tags": ["近地铁"], "facilities": []},
        ]
        ranked = rank_rooms(candidates, qr, top_n=5)
        assert len(ranked) == 2
        # Room 2 should rank higher: better budget, area, and tag match
        assert ranked[0].room_id == 2
        assert ranked[0].final_score > ranked[1].final_score

    def test_top_n_limit(self):
        qr = _make_query_result()
        candidates = [
            {"room_id": i, "rent": 1000, "district_id": 1001, "semantic_score": 0.5 + i * 0.01,
             "tags": [], "facilities": []}
            for i in range(10)
        ]
        ranked = rank_rooms(candidates, qr, top_n=3)
        assert len(ranked) == 3

    def test_recommendation_reason_present(self):
        qr = _make_query_result(
            hard_filters={"max_rent": 2000, "district_id": 1005},
            soft_preferences=["近地铁"],
        )
        candidates = [
            {"room_id": 1, "rent": 1500, "district_id": 1005, "district_name": "番禺区",
             "semantic_score": 0.85, "tags": ["近地铁"], "facilities": []},
        ]
        ranked = rank_rooms(candidates, qr)
        assert len(ranked) == 1
        assert ranked[0].recommendation_reason  # not empty
        assert "番禺" in ranked[0].recommendation_reason or "预算" in ranked[0].recommendation_reason

    def test_score_fields_populated(self):
        qr = _make_query_result(hard_filters={"max_rent": 2000})
        candidates = [
            {"room_id": 1, "rent": 1500, "district_id": 1001, "semantic_score": 0.8,
             "tags": [], "facilities": []},
        ]
        ranked = rank_rooms(candidates, qr)
        r = ranked[0]
        assert r.semantic_score > 0
        assert r.budget_score > 0
        assert r.final_score > 0
