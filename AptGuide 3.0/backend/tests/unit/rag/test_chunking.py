from aptguide3.rag.chunking import (
    build_kb_chunk_text,
    build_room_vector_record,
    build_room_vector_text,
    compute_content_hash,
    validate_kb_rule,
)


def test_compute_content_hash_deterministic():
    h1 = compute_content_hash("hello")
    h2 = compute_content_hash("hello")
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_build_room_vector_text_contains_key_fields():
    room = {
        "room_number": "302",
        "apartment_name": "大学城南亭寓",
        "rent": 1500,
        "district_name": "番禺区",
        "tags": ["安静"],
        "facilities": ["空调"],
    }
    text = build_room_vector_text(room)
    assert "302" in text
    assert "番禺区" in text
    assert "安静" in text


def test_build_room_vector_record_has_hash():
    room = {"room_id": 1, "apartment_id": 10, "rent": 1500}
    record = build_room_vector_record(room, source_version=1)
    assert record["vector_id"] == "room-1"
    assert record["content_hash"].startswith("sha256:")
    assert record["source_version"] == 1


def test_build_kb_chunk_text_includes_module_and_risk():
    rule = {
        "module": "lease", "doc_type": "policy", "title": "押金规则",
        "risk_level": "high", "content": "押金不退条件",
    }
    text = build_kb_chunk_text(rule)
    assert "lease" in text
    assert "high" in text
    assert "押金规则" in text


def test_validate_kb_rule_rejects_missing_doc_id():
    errors = validate_kb_rule({"content": "test", "status": "reviewed", "reviewed_by": "admin"})
    assert "missing doc_id" in errors


def test_validate_kb_rule_rejects_invalid_status():
    errors = validate_kb_rule({"doc_id": "KB-001", "content": "test", "status": "draft", "reviewed_by": "admin"})
    assert any("invalid status" in e for e in errors)


def test_validate_kb_rule_rejects_pii():
    errors = validate_kb_rule({
        "doc_id": "KB-001", "content": "联系电话 13800138000",
        "status": "reviewed", "reviewed_by": "admin",
    })
    assert any("PII" in e for e in errors)


def test_validate_kb_rule_accepts_valid():
    errors = validate_kb_rule({
        "doc_id": "KB-001", "content": "押金退还规则说明",
        "status": "reviewed", "reviewed_by": "admin",
    })
    assert errors == []
