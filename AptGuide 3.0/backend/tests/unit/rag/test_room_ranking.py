from __future__ import annotations

from aptguide3.rag.room_ranking import rank_rooms
from aptguide3.rag.schemas import PreferenceScore, RetrievalPlan, ValidatedRoom


def _room(room_id: int, rent: int = 1000, district_id: int | None = None, appointable: bool = True) -> ValidatedRoom:
    return ValidatedRoom(
        room_id=room_id,
        apartment_id=1,
        apartment_name="测试公寓",
        room_number=f"{room_id}01",
        district_id=district_id,
        district_name="天河区",
        rent=rent,
        is_appointable=appointable,
        semantic_score=0.8,
    )


def _plan(**kwargs) -> RetrievalPlan:
    defaults = dict(task="room_search", raw_message="找房")
    defaults.update(kwargs)
    return RetrievalPlan(**defaults)


def test_rank_rooms_returns_sorted_by_final_score():
    rooms = [_room(1, rent=1000), _room(2, rent=2000), _room(3, rent=1500)]
    plan = _plan(hard_filters={"max_rent": 1500})
    scores = {
        1: PreferenceScore(room_id=1, score=0.9, reason="偏好匹配"),
        2: PreferenceScore(room_id=2, score=0.3, reason="不太匹配"),
        3: PreferenceScore(room_id=3, score=0.6, reason="一般"),
    }
    ranked = rank_rooms(rooms, plan, scores, top_n=3)
    assert len(ranked) == 3
    assert ranked[0].final_score >= ranked[1].final_score >= ranked[2].final_score


def test_budget_scoring_under_budget():
    rooms = [_room(1, rent=800)]
    plan = _plan(hard_filters={"max_rent": 1000})
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].budget_score == 1.0


def test_budget_scoring_at_budget():
    rooms = [_room(1, rent=1000)]
    plan = _plan(hard_filters={"max_rent": 1000})
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].budget_score == 0.75


def test_budget_scoring_slightly_over_budget():
    rooms = [_room(1, rent=1050)]
    plan = _plan(hard_filters={"max_rent": 1000})
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].budget_score == 0.3


def test_budget_scoring_far_over_budget():
    rooms = [_room(1, rent=2000)]
    plan = _plan(hard_filters={"max_rent": 1000})
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].budget_score == 0.0


def test_area_scoring_matching_district():
    rooms = [_room(1, district_id=10)]
    plan = _plan(hard_filters={"district_id": 10})
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].area_score == 1.0


def test_area_scoring_non_matching_district():
    rooms = [_room(1, district_id=10)]
    plan = _plan(hard_filters={"district_id": 20})
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].area_score == 0.0


def test_area_scoring_no_target_district():
    rooms = [_room(1, district_id=10)]
    plan = _plan(hard_filters={})
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].area_score == 0.5


def test_top_n_limits_results():
    rooms = [_room(i, rent=1000) for i in range(10)]
    plan = _plan(hard_filters={})
    ranked = rank_rooms(rooms, plan, {}, top_n=3)
    assert len(ranked) == 3


def test_availability_score_appointable():
    rooms = [_room(1, appointable=True)]
    plan = _plan()
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].availability_score == 1.0


def test_availability_score_not_appointable():
    rooms = [_room(1, appointable=False)]
    plan = _plan()
    ranked = rank_rooms(rooms, plan, {}, top_n=1)
    assert ranked[0].availability_score == 0.5
