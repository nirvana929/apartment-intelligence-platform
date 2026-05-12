"""Chunking and text builders for RAG vector content.

RAG 的质量很大程度取决于“入库文本怎么写”。这个文件负责把业务数据
转换成适合 embedding 的文本，并计算 content_hash 用于增量同步。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aptguide2.rag.schemas import KBChunk, RoomVectorRecord


def compute_content_hash(content: str) -> str:
    """Compute deterministic SHA-256 hash of content."""
    # content_hash 用来判断内容是否变化。
    # 同样的内容不会重复 embedding，能节省成本并保持同步过程可追踪。
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def build_kb_chunks(rule: dict[str, Any], release_id: str) -> list[KBChunk]:
    """Build KB chunks from a YAML rule dict.

    Rules:
    - One rule becomes one chunk if content <= 800 Chinese characters.
    - Longer content splits by paragraph.
    - chunk_id format: {doc_id}#NN
    - Vector text prefix: [module][doc_type][title][tags][risk_level]
    """
    doc_id = rule["doc_id"]
    doc_type = rule.get("doc_type", "rule")
    module = rule.get("module", "lease")
    title = rule.get("title", "")
    tags = rule.get("tags", [])
    content = rule.get("content", "").strip()
    version = rule.get("version", 1)
    risk_level = rule.get("risk_level", "low")
    status = rule.get("status", "reviewed")

    if not content:
        return []

    # 长规则拆成多个 chunk，避免单个向量承载太多主题。
    # chunk 太大容易稀释语义，chunk 太小又容易缺上下文；这里先用 800 字做 MVP 阈值。
    if len(content) > 800:
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    else:
        paragraphs = [content]

    chunks = []
    tag_str = ",".join(tags) if tags else ""

    for i, paragraph in enumerate(paragraphs, start=1):
        chunk_id = f"{doc_id}#{i:02d}"
        # vector_text 是真正送去 embedding 的文本；KBChunk.content 保留原文段落。
        vector_text = _build_kb_vector_text(module, doc_type, title, tag_str, risk_level, paragraph)
        content_hash = compute_content_hash(paragraph)

        chunks.append(KBChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            doc_type=doc_type,
            module=module,
            title=title,
            tags=tags,
            content=paragraph,
            content_hash=content_hash,
            version=version,
            release_id=release_id,
            status=status,
            risk_level=risk_level,
        ))

    return chunks


def _build_kb_vector_text(
    module: str, doc_type: str, title: str, tags: str, risk_level: str, content: str
) -> str:
    """Build the text that gets embedded for a KB chunk.

    Format: title as primary signal, then content, then metadata keywords.
    """
    # 标题放在最前面：规则标题通常浓缩了用户会问的核心问题。
    parts = [title]
    # 内容提供具体规则，帮助相似问题召回到正确 chunk。
    parts.append(content)
    # tags/module 是检索增强信号，补足 embedding 对业务分类词的理解。
    if tags:
        parts.append(f"关键词：{tags}")
    module_labels = {
        "lease": "租赁合同",
        "payment": "支付费用",
        "appointment": "预约看房",
        "life": "生活服务",
        "account": "账号安全",
        "policy": "公寓政策",
        "search": "搜索找房",
    }
    if module in module_labels:
        parts.append(f"分类：{module_labels[module]}")
    return "\n".join(parts)


def build_room_vector_record(room: dict[str, Any], source_version: int) -> RoomVectorRecord:
    """Build a RoomVectorRecord from a lease sync DTO room dict.

    Text format:
    [room][广州][番禺区][大学城南亭附近]
    房间 302，位于大学城南亭寓。月租 1800 元，支持 MONTHLY, QUARTERLY，租期 6, 12 个月。
    户型 1室1卫，面积 25 平方米，标签包括 安静、可月付、近大学城、适合考研。
    公寓配套包括 空调、洗衣机、热水器、WIFI、床、书桌。
    适合希望低预算、安静学习、通勤到大学城附近的租客。
    """
    room_id = room["room_id"]
    apartment_id = room.get("apartment_id", 0)
    apartment_name = room.get("apartment_name", "")
    city_name = room.get("city_name", "广州")
    district_name = room.get("district_name", "")
    area_label = room.get("area_label", "")
    room_number = room.get("room_number", "")
    rent = room.get("rent")
    payment_types = room.get("payment_types", [])
    lease_terms = room.get("lease_terms", [])
    tags = room.get("tags", []) or []
    facilities = room.get("facilities", []) or []
    layout = room.get("layout", "")
    area = room.get("area")

    # 房源向量文本采用“结构化前缀 + 自然语言描述”。
    # 前缀帮助模型识别城市/区域，描述句帮助匹配用户口语化需求。
    lines = [
        f"[room][{city_name}][{district_name}][{area_label}]",
        _build_room_sentence(room_number, apartment_name, rent, payment_types, lease_terms),
    ]
    if layout or area:
        parts = []
        if layout:
            parts.append(f"户型 {layout}")
        if area:
            parts.append(f"面积 {area} 平方米")
        if tags:
            parts.append(f"标签包括 {'、'.join(tags)}")
        lines.append("，".join(parts) + "。")
    if facilities:
        lines.append(f"公寓配套包括 {'、'.join(facilities)}。")
    # 再追加一段 query-like 的特色摘要。
    # 用户常说“安静、有阳台、近地铁”，把标签集中放一次有助于向量匹配。
    feature_parts = []
    if tags:
        feature_parts.extend(tags)
    if facilities:
        feature_parts.extend(facilities)
    if feature_parts:
        lines.append(f"特色：{'、'.join(feature_parts)}。")

    content = "\n".join(lines)
    content_hash = compute_content_hash(content)

    return RoomVectorRecord(
        vector_id=f"room-{room_id}",
        room_id=room_id,
        apartment_id=apartment_id,
        apartment_name=apartment_name,
        city_id=room.get("city_id"),
        district_id=room.get("district_id"),
        district_name=district_name,
        rent=rent,
        payment_types=payment_types,
        lease_terms=lease_terms,
        tags=tags,
        facilities=facilities,
        profile_type="room",
        content=content,
        content_hash=content_hash,
        source_version=source_version,
        status="active",
    )


def _build_room_sentence(
    room_number: str,
    apartment_name: str,
    rent: int | None,
    payment_types: list[str],
    lease_terms: list[int],
) -> str:
    """Build the main room description sentence."""
    parts = []
    if room_number:
        parts.append(f"房间 {room_number}")
    if apartment_name:
        parts.append(f"位于{apartment_name}")
    if rent:
        parts.append(f"月租 {rent} 元")
    if payment_types:
        parts.append(f"支持 {', '.join(payment_types)}")
    if lease_terms:
        terms_str = ", ".join(str(t) for t in lease_terms)
        parts.append(f"租期 {terms_str} 个月")
    return "，".join(parts) + "。" if parts else ""
