from __future__ import annotations

import re

from aptguide2.interaction.contracts import EntityMention, InteractionIntent


AREA_ALIASES: dict[str, dict[str, object]] = {
    "大学城": {"normalized": "广州大学城", "district_id": 4, "district_name": "番禺区"},
    "广州大学城": {"normalized": "广州大学城", "district_id": 4, "district_name": "番禺区"},
    "南亭": {"normalized": "大学城南亭", "district_id": 4, "district_name": "番禺区"},
    "番禺": {"normalized": "番禺区", "district_id": 4, "district_name": "番禺区"},
    "白云": {"normalized": "白云区", "district_id": 5, "district_name": "白云区"},
    "天河": {"normalized": "天河区", "district_id": 1, "district_name": "天河区"},
    "海珠": {"normalized": "海珠区", "district_id": 3, "district_name": "海珠区"},
}

PAYMENT_ALIASES = {
    "月付": "MONTHLY",
    "季付": "QUARTERLY",
    "半年付": "SEMI_ANNUAL",
    "年付": "ANNUAL",
}


def normalize_entities(intent: InteractionIntent) -> InteractionIntent:
    hard_filters = dict(intent.hard_filters)
    soft_preferences = list(intent.soft_preferences)
    entities = list(intent.entities)
    message = intent.raw_message

    budget = _extract_budget(message)
    if budget is not None:
        hard_filters["max_rent"] = budget
        entities.append(EntityMention(kind="budget", raw_text=str(budget), normalized_value=budget, confidence=0.95, source="regex"))

    area_entity = _resolve_area(message)
    if area_entity:
        hard_filters["district_id"] = area_entity.metadata["district_id"]
        hard_filters["area_text"] = area_entity.raw_text
        entities.append(area_entity)
        area_preference = f"{area_entity.raw_text}附近"
        if "附近" in message and area_preference not in soft_preferences:
            soft_preferences.append(area_preference)
    elif "附近" in message:
        near_idx = message.index("附近") + 2
        area_text = message[:near_idx]
        if area_text not in soft_preferences:
            soft_preferences.append(area_text)

    for raw, normalized in PAYMENT_ALIASES.items():
        if raw in message:
            hard_filters["payment_type"] = normalized
            entities.append(EntityMention(kind="payment_type", raw_text=raw, normalized_value=normalized, confidence=0.95, source="alias_table"))
            break

    return intent.model_copy(update={
        "hard_filters": hard_filters,
        "soft_preferences": soft_preferences,
        "entities": entities,
    })


def _extract_budget(message: str) -> int | None:
    match = re.search(r"(\d{3,5})\s*(?:以内|以下|左右|预算)?", message)
    if not match:
        return None
    value = int(match.group(1))
    if 100 <= value <= 99999:
        return value
    return None


def _resolve_area(message: str) -> EntityMention | None:
    for alias in sorted(AREA_ALIASES, key=len, reverse=True):
        if alias in message:
            meta = AREA_ALIASES[alias]
            return EntityMention(
                kind="area",
                raw_text=alias,
                normalized_value=str(meta["normalized"]),
                confidence=0.92,
                source="alias_table",
                metadata={
                    "district_id": meta["district_id"],
                    "district_name": meta["district_name"],
                },
            )
    return None
