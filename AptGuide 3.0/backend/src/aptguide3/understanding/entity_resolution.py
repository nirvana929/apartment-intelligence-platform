"""Deterministic entity resolution between LLM extraction and data retrieval.

Bridges natural-language entities extracted by the LLM to canonical forms
used by Milvus filters, lease API queries, and ranking logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# District aliases: short form → canonical form with suffix
DISTRICT_ALIASES: dict[str, str] = {
    "天河": "天河区",
    "番禺": "番禺区",
    "黄埔": "黄埔区",
    "白云": "白云区",
    "海珠": "海珠区",
    "越秀": "越秀区",
    "荔湾": "荔湾区",
    "南沙": "南沙区",
    "花都": "花都区",
    "从化": "从化区",
    "增城": "增城区",
}

DISTRICT_SUFFIXES = ("区", "县", "市")

# Room type aliases
ROOM_TYPE_ALIASES: dict[str, str] = {
    "单间": "STUDIO",
    "单人间": "STUDIO",
    "studio": "STUDIO",
    "一房": "ONE_BEDROOM",
    "一房一厅": "ONE_BEDROOM",
    "一室": "ONE_BEDROOM",
    "两房": "TWO_BEDROOM",
    "两房一厅": "TWO_BEDROOM",
    "两室": "TWO_BEDROOM",
    "合租": "SHARED",
    "合租房": "SHARED",
    "整租": "WHOLE_RENT",
    "整租房": "WHOLE_RENT",
}

# Payment type aliases
PAYMENT_TYPE_ALIASES: dict[str, str] = {
    "月付": "MONTHLY",
    "月租": "MONTHLY",
    "按月": "MONTHLY",
    "季付": "QUARTERLY",
    "按季": "QUARTERLY",
    "半年付": "SEMI_ANNUAL",
    "半年": "SEMI_ANNUAL",
    "年付": "ANNUAL",
    "按年": "ANNUAL",
    "一年": "ANNUAL",
}


@dataclass
class EntityResolutionResult:
    """Output of entity resolution."""
    resolved_filters: dict[str, Any] = field(default_factory=dict)
    unresolved_filters: dict[str, Any] = field(default_factory=dict)
    ambiguities: list[str] = field(default_factory=list)
    resolution_notes: list[str] = field(default_factory=list)


def resolve_entities(hard_filters: dict[str, Any]) -> EntityResolutionResult:
    """Resolve LLM-extracted hard filters to canonical forms.

    Returns resolved filters ready for retrieval, plus any unresolved
    or ambiguous entities that could not be mapped.
    """
    result = EntityResolutionResult()

    for key, value in hard_filters.items():
        if value is None:
            continue

        if key == "district_name":
            resolved = _resolve_district(str(value))
            if resolved:
                result.resolved_filters["district_name"] = resolved
                if resolved != str(value):
                    result.resolution_notes.append(f"district: '{value}' → '{resolved}'")
            else:
                result.unresolved_filters["district_name"] = str(value)
                result.ambiguities.append(f"无法识别区域: '{value}'")

        elif key == "room_type":
            resolved = _resolve_room_type(str(value))
            if resolved:
                result.resolved_filters["room_type"] = resolved
                if resolved != str(value):
                    result.resolution_notes.append(f"room_type: '{value}' → '{resolved}'")
            else:
                result.unresolved_filters["room_type"] = str(value)
                result.ambiguities.append(f"无法识别房型: '{value}'")

        elif key == "payment_type":
            resolved = _resolve_payment_type(str(value))
            if resolved:
                result.resolved_filters["payment_type"] = resolved
                if resolved != str(value):
                    result.resolution_notes.append(f"payment_type: '{value}' → '{resolved}'")
            else:
                result.unresolved_filters["payment_type"] = str(value)
                result.ambiguities.append(f"无法识别付款方式: '{value}'")

        elif key in {"max_rent", "min_rent", "district_id", "apartment_id"}:
            # Numeric filters: pass through with validation
            try:
                num = int(value)
                if num > 0:
                    result.resolved_filters[key] = num
                else:
                    result.unresolved_filters[key] = value
            except (ValueError, TypeError):
                result.unresolved_filters[key] = value
                result.ambiguities.append(f"无效的数值: {key}={value}")

        elif key == "area_text":
            # Area text: pass through for semantic matching
            result.resolved_filters[key] = str(value)

        else:
            # Unknown filter key: pass through
            result.resolved_filters[key] = value

    return result


def _resolve_district(raw: str) -> str | None:
    """Normalize district name to canonical form with suffix.

    Returns None if the input cannot be confidently resolved.
    """
    raw = raw.strip()
    if not raw:
        return None

    # Already has proper suffix
    if any(raw.endswith(s) for s in DISTRICT_SUFFIXES):
        return raw

    # Check alias dictionary
    if raw in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[raw]

    # Try appending "区" as default
    return raw + "区"


def _resolve_room_type(raw: str) -> str | None:
    """Map Chinese room type to canonical enum value."""
    raw = raw.strip().lower()
    if not raw:
        return None

    # Already a canonical value
    canonical = {"studio", "one_bedroom", "two_bedroom", "shared", "whole_rent", "unknown"}
    if raw in canonical:
        return raw.upper()

    # Check aliases
    return ROOM_TYPE_ALIASES.get(raw)


def _resolve_payment_type(raw: str) -> str | None:
    """Map Chinese payment type to canonical enum value."""
    raw = raw.strip().lower()
    if not raw:
        return None

    # Already a canonical value
    canonical = {"monthly", "quarterly", "semi_annual", "annual"}
    if raw in canonical:
        return raw.upper()

    # Check aliases
    return PAYMENT_TYPE_ALIASES.get(raw)
