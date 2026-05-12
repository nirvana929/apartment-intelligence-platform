"""Deterministic MVP query understanding parser.

Extracts hard filters, soft preferences, and generates retrieval queries
from user messages without calling an LLM.

学习 RAG 时可以把这个文件理解成“检索前的结构化改写层”：
用户自然语言通常混合了任务、预算、地点、偏好、风险等信息。这里先用
规则把它们拆出来，后面的向量检索才能同时使用精确过滤和语义召回。
"""

from __future__ import annotations

import re
from typing import Any

from aptguide2.rag.schemas import QueryUnderstandingResult

# ---------------------------------------------------------------------------
# District / area mappings
# ---------------------------------------------------------------------------

DISTRICTS: dict[str, int] = {
    "天河区": 1,
    "越秀区": 2,
    "海珠区": 3,
    "番禺区": 4,
    "白云区": 5,
    "黄埔区": 6,
    "南沙区": 7,
    "花都区": 8,
    "增城区": 9,
    "从化区": 10,
    "荔湾区": 11,
    "昌平区": 110114,
}

AREA_KEYWORDS: dict[str, tuple[str, int]] = {
    "大学城": ("番禺区", 4),
    "南亭": ("番禺区", 4),
    "大学城南亭": ("番禺区", 4),
    "番禺": ("番禺区", 4),
    "天河": ("天河区", 1),
    "海珠": ("海珠区", 3),
    "越秀": ("越秀区", 2),
    "白云": ("白云区", 5),
    "客村": ("海珠区", 3),
    "琶洲": ("海珠区", 3),
    "江南西": ("海珠区", 3),
    "体育西": ("天河区", 1),
    "珠江新城": ("天河区", 1),
    "岗顶": ("天河区", 1),
    "五羊邨": ("越秀区", 2),
    "北京路": ("越秀区", 2),
    "市桥": ("番禺区", 4),
    "科韵路": ("天河区", 1),
    "昌平": ("昌平区", 110114),
}

# ---------------------------------------------------------------------------
# Payment patterns
# ---------------------------------------------------------------------------

PAYMENT_PATTERNS: dict[str, str] = {
    "月付": "MONTHLY",
    "季付": "QUARTERLY",
    "半年付": "SEMI_ANNUAL",
    "年付": "ANNUAL",
}

# ---------------------------------------------------------------------------
# Soft preference synonyms
# ---------------------------------------------------------------------------

PREFERENCE_SYNONYMS: dict[str, list[str]] = {
    "安静": ["安静", "适合学习", "低噪音"],
    "吵": ["安静", "低噪音"],
    "别太吵": ["安静", "低噪音"],
    "近地铁": ["近地铁", "交通便利", "通勤方便"],
    "通勤": ["通勤方便", "近地铁", "交通便利"],
    "考研": ["适合考研", "安静", "适合学习"],
    "学习": ["适合学习", "安静"],
    "独卫": ["独卫", "独立卫生间"],
    "独立卫浴": ["独立卫浴", "独卫"],
    "朝南": ["朝南", "采光好"],
    "采光": ["采光好", "朝南"],
    "采光好": ["采光好", "朝南"],
    "家电": ["家电齐全", "配套齐全"],
    "配套": ["配套齐全", "家电齐全"],
    "短租": ["可短租", "短租友好"],
    "月付": ["可月付"],
    "可月付": ["可月付"],
    "预算不限": [],
    "预算我都接受": [],
    "不限预算": [],
    "养宠物": ["可养宠物", "宠物友好"],
    "养猫": ["可养宠物", "宠物友好"],
    "养狗": ["可养宠物", "宠物友好"],
    "有阳台": ["有阳台", "带阳台"],
    "有厨房": ["有厨房", "可做饭"],
    "有WiFi": ["有WiFi", "有网络"],
    "有wifi": ["有WiFi", "有网络"],
    "有空调": ["有空调", "空调房"],
    "有洗衣机": ["有洗衣机"],
    "电梯": ["有电梯", "电梯房"],
    "高楼层": ["高楼层", "视野好"],
    "新装修": ["新装修", "精装修"],
    "温馨": ["温馨", "小而美"],
    "大面积": ["大面积", "宽敞"],
    "整租": ["整租", "独立空间"],
    "合租": ["合租", "单间"],
    "便宜": ["低预算", "性价比高"],
    "越便宜越好": ["低预算", "性价比高"],
}

# ---------------------------------------------------------------------------
# Budget patterns
# ---------------------------------------------------------------------------


def _cn_number_to_int(match: re.Match) -> int:
    """Convert simple Chinese number to int."""
    cn = match.group(1)
    mapping = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
               "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if cn.endswith("千"):
        base = mapping.get(cn[0], 1) if len(cn) > 1 else 1
        return base * 1000
    if cn.endswith("百"):
        base = mapping.get(cn[0], 1) if len(cn) > 1 else 1
        return base * 100
    return mapping.get(cn, 0)


BUDGET_PATTERNS = [
    # "1500以内", "2000以下", "3000左右"
    (r"(\d{3,5})\s*(?:以内|以下|以下的|左右|以下就好)", lambda m: int(m.group(1))),
    # "两千以内", "三千左右"
    (r"([一二三四五六七八九十千百]+)\s*(?:以内|以下|左右)", _cn_number_to_int),
    # "预算1500"
    (r"预算\s*(\d{3,5})", lambda m: int(m.group(1))),
]

REFERENCE_PATTERNS = [
    (r"(?:第|看)?\s*([一二三四五])\s*个", lambda m: {"index": "一二三四五".index(m.group(1))}),
    (r"刚才那个", lambda m: {"relative": "last"}),
    (r"上一个", lambda m: {"relative": "previous"}),
    (r"前面的?", lambda m: {"relative": "previous"}),
]


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def understand_query(
    message: str,
    previous_state: dict[str, Any] | None = None,
) -> QueryUnderstandingResult:
    """Parse user message into structured query understanding.

    Args:
        message: User's raw message text.
        previous_state: Previous conversation state for reference resolution
            and budget clearing detection.

    Returns:
        QueryUnderstandingResult with task, hard_filters, soft_preferences,
        retrieval_queries, and risk_level.
    """
    # previous_state 用于多轮对话继承条件，例如用户上一轮说“1500 以内”，
    # 下一轮只说“那番禺呢”，系统仍然可以保留预算约束。
    previous_state = previous_state or {}

    # 第一步：判断应该走哪条链路。
    # room_search 会查房源向量库；kb_qa 会查规则知识库；fallback 不进入 RAG。
    task = _detect_task(message)

    # hard_filters 是可被数据库/向量库精确过滤的条件。
    # RAG 中常见做法是“先过滤、再向量召回”，避免把明显不符合条件的内容召回。
    hard_filters: dict[str, Any] = {}

    # 预算是硬约束：如果用户说“1500以内”，后续 Milvus 搜索会加 rent <= 1500。
    # 如果用户明确清空预算，则写入 None；否则尝试继承上一轮状态。
    max_rent = _extract_budget(message)
    if max_rent is not None:
        hard_filters["max_rent"] = max_rent
    elif _is_budget_clearing(message):
        hard_filters["max_rent"] = None
    elif "max_rent" in previous_state and previous_state.get("max_rent") is not None:
        hard_filters["max_rent"] = previous_state["max_rent"]

    # 区域也是硬约束。area_text 保留原始区域词，district_id 用于精确过滤。
    district_info = _extract_district(message)
    if district_info:
        hard_filters["district_id"] = district_info["district_id"]
        hard_filters["area_text"] = district_info["area_text"]

    # 支付方式目前被解析出来，但房源召回过滤暂未使用它；后续可放进验证或重排。
    payment = _extract_payment(message)
    if payment:
        hard_filters["payment_type"] = payment

    # soft_preferences 是语义偏好，不适合直接过滤，否则容易漏召回。
    # 例如“适合考研”可能对应“安静 / 低噪音 / 适合学习”等标签。
    soft_preferences = _extract_preferences(message)

    # 指代解析用于识别“第一个”“刚才那个”等多轮跟进表达。
    reference_resolution = _extract_reference(message)

    # 风险等级主要服务 KB 问答：高风险问题需要更高置信度和更强来源约束。
    risk_level = _detect_risk(message)

    # 检索 query 改写：把结构化结果重新拼成更适合 embedding 的短查询。
    # 这属于 RAG 中的 query rewriting / multi-query recall。
    retrieval_queries = _generate_retrieval_queries(
        hard_filters, soft_preferences, task
    )

    return QueryUnderstandingResult(
        raw_message=message,
        task=task,
        reference_resolution=reference_resolution,
        hard_filters=hard_filters,
        soft_preferences=soft_preferences,
        retrieval_queries=retrieval_queries,
        risk_level=risk_level,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_task(message: str) -> str:
    """Detect whether this is a room search, KB question, or fallback."""
    # fallback 先判断：这些请求即使含有“房”“押金”等词，也不应该直接 RAG 回答。
    # 例如保证性承诺、法律纠纷、隐私查询等需要人工或安全兜底。
    fallback_patterns = [
        "保证", "担保", "一定", "肯定",
        "帮我写", "帮我查别人", "帮我办",
        "翻译", "股票", "投资回报",
        "和Siri", "你叫什么", "1+1",
        "黑进", "黑客", "假身份",
        "心情不好", "陪我聊天",
        "别人手机号", "其他租户",
        "甲醛", "邻居不会",
        "打官司", "纠纷你能",
        "留到下个月", "打个八折",
        "下个月会有什么优惠",
        "照片差距", "比其他品牌",
    ]
    for pat in fallback_patterns:
        if pat in message:
            return "fallback"

    kb_keywords = [
        "押金", "退租", "退房", "续租", "续约", "违约", "合同", "租约",
        "怎么退", "规则", "规定", "政策",
        "预约看房", "取消预约", "改期", "报修", "投诉",
        "隐私", "注销", "实名", "账号", "查一下别人",
        "宠物规定", "能不能养宠物", "可以养猫", "可以养狗",
        "同住人", "登记",
        "支付方式", "租金逾期", "水电费", "退款", "发票",
        "注册", "密码", "换锁", "安全注意",
        "筛选房源", "搜索结果", "照片是真的", "已租出",
        "怎么预约", "看房时间", "预约了不去", "预约好的",
        "签约流程", "签合同", "合同签多久", "续约怎么办",
        "退租要提前", "提前退租", "转租给别人",
        "维修费", "几点以后不能", "大功率电器",
        "个人信息安全", "怎么注销",
        "新用户优惠", "不满意怎么投诉", "节假日营业",
    ]
    for kw in kb_keywords:
        if kw in message:
            return "kb_qa"

    room_keywords = [
        "找房", "房子", "房源", "租房", "房间", "公寓",
        "以内", "附近", "安静", "近地铁", "独卫", "朝南",
        "月付", "季付", "考研", "通勤", "采光",
        "推荐", "有没有", "有吗", "看看",
        "单间", "一室", "两室", "合租", "整租",
        "便宜", "预算", "面积", "户型", "阳台",
        "空调", "WiFi", "wifi", "洗衣机", "独立卫浴",
        "电梯", "高楼层", "新装修", "温馨", "大面积",
        "多少钱", "什么户型", "能租到", "能租", "有房", "租到",
        "有厨房", "有阳台", "有WiFi",
        "朝南", "采光好", "视野好",
        "不想爬楼梯", "一个人住",
        "帮我找", "帮我看看",
        "种房子", "限号", "好吃的", "航班", "电影", "酒店",
    ]
    for kw in room_keywords:
        if kw in message:
            return "room_search"

    return "fallback"


def _extract_budget(message: str) -> int | None:
    """Extract max rent budget from message."""
    for pattern, extractor in BUDGET_PATTERNS:
        m = re.search(pattern, message)
        if m:
            try:
                val = extractor(m)
                if 100 <= val <= 99999:
                    return val
            except (ValueError, IndexError):
                continue
    return None


def _is_budget_clearing(message: str) -> bool:
    """Check if user is clearing their budget constraint."""
    clearing_patterns = ["预算不限", "预算我都接受", "不限预算", "预算都行", "都可以"]
    return any(p in message for p in clearing_patterns)


def _extract_district(message: str) -> dict[str, Any] | None:
    """Extract district or area from message."""
    # Check specific areas first, longest match wins
    sorted_areas = sorted(AREA_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True)
    for area, (district_name, district_id) in sorted_areas:
        if area in message:
            return {
                "district_id": district_id,
                "district_name": district_name,
                "area_text": area,
            }

    # Check district names
    for name, did in DISTRICTS.items():
        if name in message:
            return {
                "district_id": did,
                "district_name": name,
                "area_text": name,
            }

    return None


def _extract_payment(message: str) -> str | None:
    """Extract payment type from message."""
    for cn, en in PAYMENT_PATTERNS.items():
        if cn in message:
            return en
    return None


def _extract_preferences(message: str) -> list[str]:
    """Extract soft preferences from message."""
    found: list[str] = []
    for keyword, synonyms in PREFERENCE_SYNONYMS.items():
        if keyword in message:
            found.extend(synonyms)
    # 去重但保留顺序：前面的偏好通常更接近用户原始表达，后续改写时会优先使用。
    seen = set()
    result = []
    for p in found:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _extract_reference(message: str) -> dict[str, Any] | None:
    """Extract reference to previous recommendations."""
    for pattern, extractor in REFERENCE_PATTERNS:
        m = re.search(pattern, message)
        if m:
            return extractor(m)
    return None


def _detect_risk(message: str) -> str:
    """Detect risk level based on message content."""
    high_risk = ["押金", "违约金", "退租", "合同", "赔偿", "扣钱", "扣多少"]
    medium_risk = ["投诉", "纠纷", "法律", "维权"]

    for kw in high_risk:
        if kw in message:
            return "high"
    for kw in medium_risk:
        if kw in message:
            return "medium"
    return "low"


def _generate_retrieval_queries(
    hard_filters: dict[str, Any],
    soft_preferences: list[str],
    task: str,
) -> list[str]:
    """Generate up to 3 retrieval queries for vector search."""
    if task != "room_search":
        return []

    queries = []

    # Query 1 偏“用户原始条件”：地点 + 预算 + 前几个偏好 + 房源。
    # 目标是召回最直接匹配用户输入的房源。
    parts = []
    area = hard_filters.get("area_text", "")
    if area:
        parts.append(f"{area}附近")
    budget = hard_filters.get("max_rent")
    if budget:
        parts.append(f"{budget}以内")
    parts.extend(soft_preferences[:3])
    parts.append("房源")
    if parts:
        queries.append(" ".join(parts))

    # Query 2 偏“结构化检索词”：行政区 + 低预算/偏好 + 单间。
    # 目标是补足用户没说完整但业务上常见的租房表达。
    district = hard_filters.get("district_name", hard_filters.get("area_text", ""))
    if district:
        parts2 = [district]
        if budget:
            parts2.append(f"低预算")
        if soft_preferences:
            parts2.append(soft_preferences[0])
        parts2.append("单间")
        queries.append(" ".join(parts2))

    # Query 3 偏“生活方式画像”：考研、通勤等人群语义常常比标签字面更好匹配。
    if soft_preferences:
        parts3 = ["适合"]
        if "适合考研" in soft_preferences or "适合学习" in soft_preferences:
            parts3 = ["适合考研学生"]
        elif "通勤方便" in soft_preferences or "近地铁" in soft_preferences:
            parts3 = ["适合白领通勤"]
        parts3.extend(soft_preferences[:2])
        parts3.append("公寓")
        queries.append(" ".join(parts3))

    return queries[:3]
