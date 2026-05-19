from __future__ import annotations

import hashlib
import json
import re
from typing import Any

PII_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),           # phone
    re.compile(r"\d{17}[\dXx]"),           # ID card
    re.compile(r"\d{16,19}"),              # bank card
]


def compute_content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _list_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "、".join(str(item) for item in value if item)
    return str(value)


def build_room_vector_text(room: dict) -> str:
    tags = _list_text(room.get("tags"))
    facilities = _list_text(room.get("facilities"))
    payment_types = _list_text(room.get("payment_types"))
    lease_terms = _list_text(room.get("lease_terms"))
    return "\n".join([
        (
            f"[room][{room.get('city_name', '')}][{room.get('district_name', '')}]"
            f"[{room.get('area_label', '')}]"
        ),
        (
            f"房间 {room.get('room_number', '')}，位于 {room.get('apartment_name', '')}。"
            f"月租 {room.get('rent', '')} 元，支持付款方式：{payment_types}，"
            f"租期：{lease_terms}。"
        ),
        (
            f"户型 {room.get('layout', '')}，面积 {room.get('area', '')}。"
            f"标签：{tags}。设施：{facilities}。"
        ),
    ]).strip()


def build_kb_chunk_text(rule: dict) -> str:
    tags = _list_text(rule.get("tags"))
    return (
        f"[{rule.get('module', '')}][{rule.get('doc_type', '')}]"
        f"[{rule.get('title', '')}][{tags}][{rule.get('risk_level', 'low')}]\n"
        f"{rule.get('content', '')}"
    ).strip()


def build_room_vector_record(room: dict, source_version: int) -> dict:
    content = build_room_vector_text(room)
    return {
        "vector_id": f"room-{room.get('room_id')}",
        "room_id": int(room.get("room_id", 0)),
        "apartment_id": int(room.get("apartment_id", 0)),
        "apartment_name": room.get("apartment_name", ""),
        "city_id": room.get("city_id"),
        "district_id": room.get("district_id"),
        "district_name": room.get("district_name", ""),
        "rent": room.get("rent"),
        "payment_types": room.get("payment_types") or [],
        "lease_terms": room.get("lease_terms") or [],
        "tags": room.get("tags") or [],
        "facilities": room.get("facilities") or [],
        "profile_type": "room",
        "content": content,
        "content_hash": compute_content_hash(json.dumps(room, ensure_ascii=False, sort_keys=True)),
        "source_version": source_version,
        "status": "active",
    }


def validate_kb_rule(rule: dict) -> list[str]:
    errors: list[str] = []
    if not rule.get("doc_id"):
        errors.append("missing doc_id")
    status = rule.get("status", "")
    if status not in ("reviewed", "approved", "active"):
        errors.append(f"invalid status: {status}")
    if not rule.get("reviewed_by"):
        errors.append("missing reviewed_by")
    module = rule.get("module", "")
    risk_level = rule.get("risk_level", "")
    if module in ("lease", "payment", "account") and not risk_level:
        errors.append("high-risk module missing risk_level")
    content = rule.get("content", "")
    for pattern in PII_PATTERNS:
        if pattern.search(content):
            errors.append(f"PII detected: {pattern.pattern}")
    return errors
