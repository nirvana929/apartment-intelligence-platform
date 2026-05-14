"""Tests for query understanding."""

from aptguide2.rag.query_understanding import understand_query

# ---------------------------------------------------------------------------
# Task detection
# ---------------------------------------------------------------------------

def test_detect_room_search():
    r = understand_query("找大学城南亭附近1500以内安静点的房子")
    assert r.task == "room_search"


def test_detect_kb_qa_deposit():
    r = understand_query("押金退还多久到账")
    assert r.task == "kb_qa"


def test_detect_kb_qa_early_termination():
    r = understand_query("提前退租会扣多少钱")
    assert r.task == "kb_qa"


def test_detect_kb_qa_privacy():
    r = understand_query("能查一下别人租约吗")
    assert r.task == "kb_qa"


def test_detect_fallback():
    r = understand_query("今天天气怎么样")
    assert r.task == "fallback"


# ---------------------------------------------------------------------------
# Budget extraction
# ---------------------------------------------------------------------------

def test_budget_numeric():
    r = understand_query("找1500以内的房子")
    assert r.hard_filters.get("max_rent") == 1500


def test_budget_larger():
    r = understand_query("天河区3000以内可月付")
    assert r.hard_filters.get("max_rent") == 3000


def test_budget_around():
    r = understand_query("2000左右的")
    assert r.hard_filters.get("max_rent") == 2000


def test_budget_clearing():
    r = understand_query("预算我都接受", previous_state={"max_rent": 1500})
    assert r.hard_filters.get("max_rent") is None


def test_budget_no_budget():
    r = understand_query("找安静点的房子")
    assert "max_rent" not in r.hard_filters


# ---------------------------------------------------------------------------
# District / area extraction
# ---------------------------------------------------------------------------

def test_district_tianhe():
    r = understand_query("天河区3000以内")
    assert r.hard_filters.get("district_id") == 1


def test_area_university_town():
    r = understand_query("找大学城南亭附近1500以内安静点的")
    assert r.hard_filters.get("area_text") == "大学城南亭"
    assert r.hard_filters.get("district_id") == 4


def test_district_panyu():
    r = understand_query("番禺区的房源")
    assert r.hard_filters.get("district_id") == 4


# ---------------------------------------------------------------------------
# Payment extraction
# ---------------------------------------------------------------------------

def test_payment_monthly():
    r = understand_query("天河区3000以内可月付")
    assert r.hard_filters.get("payment_type") == "MONTHLY"


def test_payment_quarterly():
    r = understand_query("季付的房子")
    assert r.hard_filters.get("payment_type") == "QUARTERLY"


# ---------------------------------------------------------------------------
# Soft preferences
# ---------------------------------------------------------------------------

def test_preference_quiet():
    r = understand_query("找安静点的房子")
    assert "安静" in r.soft_preferences
    assert "低噪音" in r.soft_preferences


def test_preference_subway():
    r = understand_query("近地铁通勤方便")
    assert "近地铁" in r.soft_preferences
    assert "通勤方便" in r.soft_preferences


def test_preference_grad_school():
    r = understand_query("考研安静学习")
    assert "适合考研" in r.soft_preferences
    assert "安静" in r.soft_preferences


# ---------------------------------------------------------------------------
# Reference resolution
# ---------------------------------------------------------------------------

def test_reference_first():
    r = understand_query("第一个")
    assert r.reference_resolution == {"index": 0}


def test_reference_last():
    r = understand_query("刚才那个")
    assert r.reference_resolution == {"relative": "last"}


# ---------------------------------------------------------------------------
# Risk level
# ---------------------------------------------------------------------------

def test_risk_high_deposit():
    r = understand_query("押金退还多久到账")
    assert r.risk_level == "high"


def test_risk_low_search():
    r = understand_query("找安静点的房子")
    assert r.risk_level == "low"


# ---------------------------------------------------------------------------
# Retrieval queries
# ---------------------------------------------------------------------------

def test_retrieval_queries_generated():
    r = understand_query("找大学城南亭附近1500以内安静点的")
    assert len(r.retrieval_queries) > 0
    assert len(r.retrieval_queries) <= 3


def test_retrieval_queries_empty_for_kb():
    r = understand_query("押金退还多久到账")
    assert r.retrieval_queries == []


# ---------------------------------------------------------------------------
# Complex cases
# ---------------------------------------------------------------------------

def test_complex_room_search():
    r = understand_query("找大学城南亭附近1500以内安静点的房子")
    assert r.task == "room_search"
    assert r.hard_filters.get("max_rent") == 1500
    assert r.hard_filters.get("area_text") == "大学城南亭"
    assert "安静" in r.soft_preferences


def test_complex_with_payment():
    r = understand_query("天河区3000以内可月付，通勤方便")
    assert r.task == "room_search"
    assert r.hard_filters.get("district_id") == 1
    assert r.hard_filters.get("max_rent") == 3000
    assert r.hard_filters.get("payment_type") == "MONTHLY"
    assert "通勤方便" in r.soft_preferences
