"""Tests for chunking and text builders."""

from aptguide2.rag.chunking import (
    build_kb_chunks,
    build_room_vector_record,
    compute_content_hash,
)

# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------

def test_content_hash_deterministic():
    h1 = compute_content_hash("押金退还以验房为前提")
    h2 = compute_content_hash("押金退还以验房为前提")
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_content_hash_different_content():
    h1 = compute_content_hash("abc")
    h2 = compute_content_hash("def")
    assert h1 != h2


# ---------------------------------------------------------------------------
# KB chunks
# ---------------------------------------------------------------------------

KB_RULE = {
    "doc_id": "KB-LEASE-005",
    "doc_type": "rule",
    "module": "lease",
    "title": "押金退还规则",
    "tags": ["押金", "退租", "扣费"],
    "content": "押金退还以退租验房、费用结清和合同约定为前提。若存在未结清费用、设施损坏或违约事项，可能按合同和门店规则扣除相应费用。具体到账时间以门店处理和支付渠道为准。",
    "version": 1,
    "risk_level": "high",
    "status": "reviewed",
}


def test_build_kb_chunks_single():
    chunks = build_kb_chunks(KB_RULE, release_id="20260511-001")
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.chunk_id == "KB-LEASE-005#01"
    assert chunk.doc_id == "KB-LEASE-005"
    assert chunk.module == "lease"
    assert chunk.risk_level == "high"
    assert chunk.status == "reviewed"
    assert chunk.release_id == "20260511-001"
    assert chunk.content_hash.startswith("sha256:")


def test_build_kb_chunks_long_content_splits():
    long_content = "\n\n".join([f"段落{i}。" * 100 for i in range(5)])
    rule = {**KB_RULE, "content": long_content}
    chunks = build_kb_chunks(rule, release_id="r1")
    assert len(chunks) == 5
    assert chunks[0].chunk_id == "KB-LEASE-005#01"
    assert chunks[4].chunk_id == "KB-LEASE-005#05"


def test_build_kb_chunks_empty_content():
    rule = {**KB_RULE, "content": ""}
    assert build_kb_chunks(rule, release_id="r1") == []


def test_build_kb_chunks_deterministic_hash():
    c1 = build_kb_chunks(KB_RULE, release_id="r1")
    c2 = build_kb_chunks(KB_RULE, release_id="r1")
    assert c1[0].content_hash == c2[0].content_hash


# ---------------------------------------------------------------------------
# Room vector record
# ---------------------------------------------------------------------------

ROOM_DTO = {
    "room_id": 3001,
    "apartment_id": 2001,
    "city_id": 4401,
    "city_name": "广州",
    "district_id": 1005,
    "district_name": "番禺区",
    "area_label": "大学城南亭附近",
    "room_number": "302",
    "apartment_name": "大学城南亭寓",
    "rent": 1800,
    "area": 25,
    "layout": "1室1卫",
    "payment_types": ["MONTHLY", "QUARTERLY"],
    "lease_terms": [6, 12],
    "tags": ["安静", "可月付", "近大学城", "适合考研"],
    "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌"],
}


def test_build_room_vector_record():
    rec = build_room_vector_record(ROOM_DTO, source_version=1)
    assert rec.vector_id == "room-3001"
    assert rec.room_id == 3001
    assert rec.apartment_id == 2001
    assert rec.district_name == "番禺区"
    assert rec.rent == 1800
    assert rec.status == "active"
    assert rec.profile_type == "room"
    assert rec.source_version == 1
    assert "安静" in rec.tags
    assert "MONTHLY" in rec.payment_types


def test_build_room_vector_record_content():
    rec = build_room_vector_record(ROOM_DTO, source_version=1)
    assert "[room][广州][番禺区][大学城南亭附近]" in rec.content
    assert "1800" in rec.content
    assert "安静" in rec.content


def test_build_room_vector_record_hash_deterministic():
    r1 = build_room_vector_record(ROOM_DTO, source_version=1)
    r2 = build_room_vector_record(ROOM_DTO, source_version=2)
    assert r1.content_hash == r2.content_hash
    assert r1.source_version != r2.source_version


def test_build_room_vector_record_minimal():
    minimal = {"room_id": 4001, "apartment_id": 3001}
    rec = build_room_vector_record(minimal, source_version=1)
    assert rec.room_id == 4001
    assert rec.content_hash.startswith("sha256:")
