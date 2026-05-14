from aptguide2.interaction.entity_resolution import normalize_entities
from aptguide2.interaction.contracts import InteractionIntent


def test_university_town_alias_becomes_standard_district_and_soft_area():
    intent = InteractionIntent(raw_message="大学城附近1500以内的安静房源")

    normalized = normalize_entities(intent)

    assert normalized.hard_filters["district_id"] == 4
    assert normalized.hard_filters["max_rent"] == 1500
    assert "大学城附近" in normalized.soft_preferences
    area = [e for e in normalized.entities if e.kind == "area"][0]
    assert area.raw_text == "大学城"
    assert area.normalized_value == "广州大学城"
    assert area.metadata["district_id"] == 4


def test_baiyun_alias_normalizes_to_district_five():
    intent = InteractionIntent(raw_message="白云大面积低预算")

    normalized = normalize_entities(intent)

    assert normalized.hard_filters["district_id"] == 5


def test_unknown_area_stays_soft_preference_not_hard_filter():
    intent = InteractionIntent(raw_message="彩虹桥附近找房")

    normalized = normalize_entities(intent)

    assert "district_id" not in normalized.hard_filters
    assert "彩虹桥附近" in normalized.soft_preferences
