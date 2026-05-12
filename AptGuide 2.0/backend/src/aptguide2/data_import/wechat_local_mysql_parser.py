from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WechatMessageBlock:
    source_file: str
    source_group: str
    message_time: str
    sender_alias: str
    message_type: str
    body: str
    content_hash: str


DISTRICT_KEYWORDS = {
    "天河区": ["天河", "黄村", "珠村", "棠下", "棠东", "上社", "车陂", "科韵路", "员村", "体育西", "珠江新城"],
    "番禺区": ["番禺", "大石", "市桥", "南村万博", "汉溪长隆", "大学城", "广州南站"],
    "白云区": ["白云", "鹤边", "马务", "嘉禾", "嘉禾望岗", "新市", "沙贝", "横沙"],
    "荔湾区": ["荔湾", "菊树", "西塱", "坑口", "芳村", "黄沙", "上下九"],
    "海珠区": ["海珠", "客村", "琶洲", "昌岗", "沙园", "凤凰新村", "中大", "鹭江", "赤岗"],
    "越秀区": ["越秀", "北京路", "公园前", "淘金", "小北", "东山口"],
}

TAG_KEYWORDS = {
    "房东直租": ["房东直租", "自家新房"],
    "无中介费": ["无中介费", "0中介费"],
    "近地铁": ["地铁", "分钟到地铁"],
    "民水民电": ["民水民电", "民水电"],
    "押一付一": ["押一付一"],
    "可短租": ["可短租", "短租"],
    "不短租": ["不短租"],
    "宠物友好": ["可养猫", "宠物友好", "养猫"],
    "采光好": ["采光好", "阳光", "光线好", "光线充足"],
    "家电齐全": ["家电齐全", "家具齐全", "拎包入住", "领包入住"],
    "独卫": ["独卫", "独立卫生间", "独立洗手间", "洗手间"],
    "阳台": ["阳台", "独立阳台"],
}

PAYMENT_TAGS = ["押一付一", "可月付", "月付"]
FACILITY_TAGS = ["空调", "洗衣机", "热水器", "冰箱", "密码锁", "门禁", "监控", "电梯", "停车场"]
METRO_LINE_PATTERN = re.compile(r"(?<!\d)(\d{1,2})号线")
HEADER_PATTERN = re.compile(
    r"^\[(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s+"
    r"(?P<sender>.*?)\s+\((?P<type>[^)]+)\):\s*(?P<body>.*)$",
    re.S | re.M,
)
PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
WECHAT_PATTERN = re.compile(
    r"(?:微信|加V|加v|微)[/电话同步同号：:\s]*([A-Za-z0-9_-]{4,})"
)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\\n", "\n")
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_source_group(text: str) -> str:
    first_lines = [line.strip() for line in text.splitlines()[:5] if line.strip()]
    for line in first_lines:
        if "广州租房群A134" in line:
            return "广州租房群A134-禁中介"
    return "UNKNOWN_WECHAT_GROUP"


def parse_message_blocks(text: str, source_file: str) -> list[WechatMessageBlock]:
    source_group = parse_source_group(text)
    blocks: list[WechatMessageBlock] = []
    for raw_block in text.split("---"):
        block = raw_block.strip()
        if not block:
            continue
        match = HEADER_PATTERN.search(block)
        if not match:
            continue
        body = normalize_text(match.group("body"))
        content_hash = sha256_text(f"{match.group('time')}|{match.group('sender')}|{body}")
        blocks.append(
            WechatMessageBlock(
                source_file=source_file,
                source_group=source_group,
                message_time=match.group("time"),
                sender_alias=match.group("sender").strip(),
                message_type=match.group("type").strip(),
                body=body,
                content_hash=content_hash,
            )
        )
    return blocks


def redact_media_urls(text: str) -> str:
    value = re.sub(r"http://127\.0\.0\.1:5030/\S+", "[MEDIA]", text)
    value = re.sub(r"msg\\(?:attach|video)\\\S+", "[MEDIA]", value)
    return value


def redact_contacts(text: str) -> str:
    value = PHONE_PATTERN.sub("[PHONE]", text)
    value = WECHAT_PATTERN.sub("[WECHAT]", value)
    return value


def extract_contacts(text: str) -> dict[str, list[str] | str | None]:
    phone_numbers = sorted(set(PHONE_PATTERN.findall(text)))
    wechat_ids = sorted(set(WECHAT_PATTERN.findall(text)))
    contact_parts = []
    if phone_numbers:
        contact_parts.append("电话：" + "、".join(phone_numbers))
    if wechat_ids:
        contact_parts.append("微信：" + "、".join(wechat_ids))
    # Also capture the raw contact sentence for reference
    contact_lines = []
    for line in text.split("\n"):
        line_lower = line.lower()
        if any(kw in line_lower for kw in ["电话", "微信", "加v", "联系方式", "同步"]) and (
            PHONE_PATTERN.search(line) or WECHAT_PATTERN.search(line)
        ):
            contact_lines.append(line.strip())
    contact_text = "；".join(contact_lines) if contact_lines else "；".join(contact_parts)
    return {
        "phone_numbers": phone_numbers,
        "wechat_ids": wechat_ids,
        "contact_text": contact_text or None,
    }


def extract_district_and_area(text: str) -> tuple[str | None, str | None, list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    matches: list[tuple[str, int, str]] = []
    for district, keywords in DISTRICT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                matches.append((district, len(keyword), keyword))
    if not matches:
        return None, None, warnings
    matches.sort(key=lambda item: item[1], reverse=True)
    selected_district = matches[0][0]
    selected_keywords = []
    for district, _score, keyword in matches:
        if district == selected_district and keyword not in selected_keywords and keyword != selected_district[:2]:
            selected_keywords.append(keyword)
    area_label = "/".join(selected_keywords[:3]) if selected_keywords else None
    matched_districts = sorted({item[0] for item in matches})
    if len(matched_districts) > 1:
        warnings.append(
            {
                "code": "MULTIPLE_DISTRICT_MATCH",
                "message": f"Matched {', '.join(matched_districts)}; selected {selected_district}.",
            }
        )
    return selected_district, area_label, warnings


def normalize_layout(raw: str) -> str:
    if raw in {"一房", "1房", "一室一厅", "一房一厅", "1房1厅"}:
        return "一房一厅"
    if raw in {"两房", "二房", "2房", "两室一厅", "两房一厅", "二房一厅", "2房1厅"}:
        return "两房一厅"
    return "单间"


def extract_layouts(text: str) -> list[dict[str, int | str | None]]:
    pattern_after = re.compile(
        r"(?P<layout>大?单间|一室一厅|一房一厅|1房1厅|一房|1房|两室一厅|两房一厅|二房一厅|2房1厅|两房|二房|2房)"
        r"[^0-9]{0,12}"
        r"(?P<min>\d{3,5})"
        r"(?:\s*(?:-|--|到|至|~|～)\s*(?P<max>\d{3,5}))?"
        r"\s*(?:起)?"
    )
    pattern_before = re.compile(
        r"(?P<min>\d{3,5})"
        r"(?:\s*(?:-|--|到|至|~|～)\s*(?P<max>\d{3,5}))?"
        r"\s*(?:起)?"
        r"[^0-9]{1,12}"
        r"(?P<layout>大?单间|一室一厅|一房一厅|1房1厅|一房|1房|两室一厅|两房一厅|二房一厅|2房1厅|两房|二房|2房)"
    )
    layouts: list[dict[str, int | str | None]] = []
    seen = set()
    for pattern in [pattern_after, pattern_before]:
        for match in pattern.finditer(text):
            rent_min = int(match.group("min"))
            rent_max = int(match.group("max")) if match.group("max") else None
            if rent_min < 300 or rent_min > 20000 or (rent_max is not None and rent_max > 20000):
                continue
            layout = normalize_layout(match.group("layout"))
            key = (layout, rent_min, rent_max)
            if key in seen:
                continue
            seen.add(key)
            layouts.append({"layout": layout, "rent_min": rent_min, "rent_max": rent_max})
    return layouts


def extract_metro_lines(text: str) -> list[str]:
    return sorted({f"{line}号线" for line in METRO_LINE_PATTERN.findall(text)}, key=lambda item: int(item[:-2]))


def extract_metro_stations(text: str) -> list[str]:
    stations = []
    for keywords in DISTRICT_KEYWORDS.values():
        for keyword in keywords:
            if keyword in text and keyword not in stations and keyword not in {"天河", "番禺", "白云", "荔湾", "海珠", "越秀"}:
                stations.append(keyword)
    return stations[:8]


def extract_tags(text: str) -> tuple[list[str], list[str], list[str]]:
    rental_tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            rental_tags.append(tag)
    if "不短租" in rental_tags and "可短租" in rental_tags:
        rental_tags.remove("可短租")
    payment_tags = [tag for tag in PAYMENT_TAGS if tag in text]
    facility_tags = [tag for tag in FACILITY_TAGS if tag in text]
    return payment_tags, facility_tags, rental_tags


def build_description(
    text: str,
    district: str | None,
    area: str | None,
    layouts: list[dict[str, Any]],
) -> str:
    parts = []
    if district or area:
        parts.append(f"{district or ''}{area or ''}附近真实发布租房线索")
    if layouts:
        layout_text = "，".join(
            f"{item['layout']}{item['rent_min']}-{item['rent_max']}" if item.get("rent_max") else f"{item['layout']}{item['rent_min']}起"
            for item in layouts[:4]
        )
        parts.append(layout_text)
    for keyword in ["房东直租", "无中介费", "民水民电", "押一付一", "近地铁", "家电齐全", "采光好"]:
        if keyword in text:
            parts.append(keyword)
    description = "，".join(parts) or redact_media_urls(text)[:180]
    return description


def extract_listing(
    *,
    source_file: str,
    source_group: str,
    message_time: str,
    sender_alias: str,
    message_type: str,
    body: str,
) -> dict[str, Any] | None:
    normalized = normalize_text(body)
    media_redacted = redact_media_urls(normalized)
    safe_for_layout = redact_contacts(media_redacted)
    layouts = extract_layouts(safe_for_layout)
    district, area_label, warnings = extract_district_and_area(media_redacted)
    metro_lines = extract_metro_lines(media_redacted)
    metro_stations = extract_metro_stations(media_redacted)
    if not layouts:
        return None
    if not any([district, area_label, metro_stations]):
        return None

    rent_values = []
    for item in layouts:
        rent_values.append(int(item["rent_min"]))
        if item.get("rent_max") is not None:
            rent_values.append(int(item["rent_max"]))
    rent_min = min(rent_values)
    rent_max = max(rent_values)
    if rent_min < 300 or rent_max > 20000:
        return None

    contacts = extract_contacts(normalized)
    payment_tags, facility_tags, rental_tags = extract_tags(media_redacted)
    description = build_description(media_redacted, district, area_label, layouts)

    source_message_hash = sha256_text(f"{message_time}|{sender_alias}|{body}")
    dedupe_key = sha256_text(
        json.dumps(
            {
                "district": district,
                "area": area_label,
                "layouts": layouts,
                "description": description,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return {
        "source_type": "WECHAT_GROUP",
        "authenticity": "REAL_POSTED",
        "verification_status": "UNVERIFIED",
        "availability_status": "UNKNOWN",
        "source_file": source_file,
        "source_group": source_group,
        "source_message_hash": source_message_hash,
        "message_time": message_time,
        "sender_alias": sender_alias,
        "message_type": message_type,
        "city_name": "广州市",
        "district_name": district,
        "area_label": area_label,
        "metro_lines": metro_lines,
        "metro_stations": metro_stations,
        "layouts": layouts,
        "rent_min": rent_min,
        "rent_max": rent_max,
        "payment_tags": payment_tags,
        "facility_tags": facility_tags,
        "rental_tags": rental_tags,
        "phone_numbers": contacts["phone_numbers"],
        "wechat_ids": contacts["wechat_ids"],
        "contact_text": contacts["contact_text"],
        "description_text": description,
        "raw_text": normalized,
        "is_active": True,
        "appointable": False,
        "dedupe_key": dedupe_key,
        "extraction_warnings": warnings,
    }
