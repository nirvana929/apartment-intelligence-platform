from __future__ import annotations

from aptguide3.understanding.entity_resolution import (
    _resolve_district,
    _resolve_payment_type,
    _resolve_room_type,
    resolve_entities,
)


class TestResolveDistrict:
    def test_already_has_suffix(self):
        assert _resolve_district("天河区") == "天河区"

    def test_short_form_alias(self):
        assert _resolve_district("番禺") == "番禺区"

    def test_all_known_aliases(self):
        for short, full in [
            ("天河", "天河区"), ("番禺", "番禺区"), ("黄埔", "黄埔区"),
            ("白云", "白云区"), ("海珠", "海珠区"), ("越秀", "越秀区"),
            ("荔湾", "荔湾区"), ("南沙", "南沙区"), ("花都", "花都区"),
            ("从化", "从化区"), ("增城", "增城区"),
        ]:
            assert _resolve_district(short) == full

    def test_unknown_district_appends_suffix(self):
        assert _resolve_district("未知区名") == "未知区名区"

    def test_empty_returns_none(self):
        assert _resolve_district("") is None


class TestResolveRoomType:
    def test_canonical_values(self):
        assert _resolve_room_type("STUDIO") == "STUDIO"
        assert _resolve_room_type("ONE_BEDROOM") == "ONE_BEDROOM"

    def test_chinese_aliases(self):
        assert _resolve_room_type("单间") == "STUDIO"
        assert _resolve_room_type("一房") == "ONE_BEDROOM"
        assert _resolve_room_type("两房") == "TWO_BEDROOM"
        assert _resolve_room_type("合租") == "SHARED"
        assert _resolve_room_type("整租") == "WHOLE_RENT"

    def test_unknown_returns_none(self):
        assert _resolve_room_type("别墅") is None


class TestResolvePaymentType:
    def test_canonical_values(self):
        assert _resolve_payment_type("MONTHLY") == "MONTHLY"

    def test_chinese_aliases(self):
        assert _resolve_payment_type("月付") == "MONTHLY"
        assert _resolve_payment_type("季付") == "QUARTERLY"
        assert _resolve_payment_type("半年付") == "SEMI_ANNUAL"
        assert _resolve_payment_type("年付") == "ANNUAL"

    def test_unknown_returns_none(self):
        assert _resolve_payment_type("周付") is None


class TestResolveEntities:
    def test_empty_filters(self):
        result = resolve_entities({})
        assert result.resolved_filters == {}
        assert result.unresolved_filters == {}
        assert result.ambiguities == []

    def test_district_resolution(self):
        result = resolve_entities({"district_name": "番禺"})
        assert result.resolved_filters["district_name"] == "番禺区"
        assert "district: '番禺' → '番禺区'" in result.resolution_notes

    def test_rent_passthrough(self):
        result = resolve_entities({"max_rent": 2000, "min_rent": 500})
        assert result.resolved_filters["max_rent"] == 2000
        assert result.resolved_filters["min_rent"] == 500

    def test_invalid_rent(self):
        result = resolve_entities({"max_rent": "abc"})
        assert "max_rent" in result.unresolved_filters
        assert any("无效" in a for a in result.ambiguities)

    def test_room_type_resolution(self):
        result = resolve_entities({"room_type": "单间"})
        assert result.resolved_filters["room_type"] == "STUDIO"

    def test_payment_type_resolution(self):
        result = resolve_entities({"payment_type": "月付"})
        assert result.resolved_filters["payment_type"] == "MONTHLY"

    def test_combined_filters(self):
        result = resolve_entities({
            "district_name": "天河",
            "max_rent": 2000,
            "room_type": "单间",
            "payment_type": "季付",
        })
        assert result.resolved_filters["district_name"] == "天河区"
        assert result.resolved_filters["max_rent"] == 2000
        assert result.resolved_filters["room_type"] == "STUDIO"
        assert result.resolved_filters["payment_type"] == "QUARTERLY"
        assert result.unresolved_filters == {}

    def test_none_values_skipped(self):
        result = resolve_entities({"district_name": None, "max_rent": None})
        assert "district_name" not in result.resolved_filters
        assert "max_rent" not in result.resolved_filters

    def test_area_text_passthrough(self):
        result = resolve_entities({"area_text": "珠江新城附近"})
        assert result.resolved_filters["area_text"] == "珠江新城附近"
