from pydantic import ValidationError

from aptguide2.interaction.contracts import EntityMention, InteractionIntent


def test_interaction_intent_defaults_are_safe():
    intent = InteractionIntent(raw_message="入住要准备啥")

    assert intent.route == "fallback"
    assert intent.rag_task == "none"
    assert intent.domain == "unknown"
    assert intent.action == "unknown"
    assert intent.confidence == 0.0
    assert intent.hard_filters == {}
    assert intent.soft_preferences == []
    assert intent.needs_confirmation is False


def test_interaction_intent_supports_normalized_entities():
    intent = InteractionIntent(
        raw_message="大学城附近1500以内",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        hard_filters={"district_id": 4, "max_rent": 1500},
        soft_preferences=["大学城附近"],
        entities=[
            EntityMention(
                kind="area",
                raw_text="大学城",
                normalized_value="广州大学城",
                confidence=0.92,
                source="alias_table",
                metadata={"district_id": 4},
            )
        ],
        confidence=0.9,
    )

    assert intent.entities[0].normalized_value == "广州大学城"
    assert intent.hard_filters["district_id"] == 4


def test_interaction_intent_supports_llm_retrieval_queries_and_clarification_flag():
    intent = InteractionIntent(
        raw_message="越秀区3000以内有阳台的房间",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.91,
        hard_filters={"district_id": 2, "area_text": "越秀", "max_rent": 3000},
        soft_preferences=["有阳台"],
        retrieval_queries=["越秀 3000以内 有阳台 房源"],
        clarification_needed=False,
    )

    assert intent.retrieval_queries == ["越秀 3000以内 有阳台 房源"]
    assert intent.clarification_needed is False


def test_interaction_intent_rejects_invalid_confidence():
    try:
        InteractionIntent(raw_message="x", confidence=1.2)
    except ValidationError:
        return

    raise AssertionError("confidence above 1.0 must fail Pydantic validation")
