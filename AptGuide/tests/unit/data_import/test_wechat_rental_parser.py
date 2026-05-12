from aptguide.data_import.wechat_rental_parser import (
    extract_listing,
    parse_message_blocks,
    redact_sensitive_text,
)


def test_parse_message_blocks_keeps_text_message_body():
    text = """群名称: 广州租房群A134-禁中介
消息数量: 2

[2026-05-06 15:43] 广州房东直租 (text): 🏠 天河棠下-上社房东自建屋
单间680-950
一房980-1580
电话同步18620724159
---
[2026-05-06 15:44] 李新 (image): ![图片](http://127.0.0.1:5030/image/x)
---"""

    blocks = parse_message_blocks(text, "sample.txt")

    assert len(blocks) == 2
    assert blocks[0].message_time == "2026-05-06 15:43"
    assert blocks[0].message_type == "text"
    assert "天河棠下" in blocks[0].body
    assert blocks[1].message_type == "image"


def test_redact_sensitive_text_removes_phone_wechat_and_local_media_url():
    raw = "请加微信 18998438337，微信/电话同号：abc12345 http://127.0.0.1:5030/image/x"

    redacted = redact_sensitive_text(raw)

    assert "18998438337" not in redacted
    assert "abc12345" not in redacted
    assert "127.0.0.1" not in redacted
    assert "[REDACTED_CONTACT]" in redacted


def test_extract_listing_from_realistic_tianhe_post():
    body = """天河黄村4/21珠村13号线三地铁线房东直租
✅ 步行6分钟到地铁
✅ 房东直租 无中介费
✅ 民水民电 电费才0.88/度
✅ 押一付一
599起拿下阳光大单间
699起住一房一厅
支持视频看房
联系方式：15202955805（微信同步）"""

    listing = extract_listing(
        source_file="sample.txt",
        source_group="广州租房群A134-禁中介",
        message_time="2026-04-30 06:34",
        sender_alias="爱杰的可可",
        body=body,
    )

    assert listing is not None
    assert listing["source_type"] == "WECHAT_GROUP"
    assert listing["authenticity"] == "REAL_POSTED"
    assert listing["verification_status"] == "UNVERIFIED"
    assert listing["availability_status"] == "UNKNOWN"
    assert listing["district_name"] == "天河区"
    assert listing["area_label"] == "黄村/珠村"
    assert listing["rent_min"] == 599
    assert listing["rent_max"] == 699
    assert {"单间", "一房一厅"} == {item["layout"] for item in listing["layouts"]}
    assert "押一付一" in listing["payment_tags"]
    assert "民水民电" in listing["rental_tags"]
    assert listing["rag_visible"] is True
    assert listing["appointable"] is False
    assert "15202955805" not in listing["description_sanitized"]


def test_extract_listing_respects_no_short_rent_conflict():
    body = """不短租~~荔湾区菊树地铁站
单间750--1100家电齐全
一室一厅:750-1300家电齐全
走路到菊树地铁口5分钟内
请加微信 18998438337微信"""

    listing = extract_listing(
        source_file="sample.txt",
        source_group="广州租房群A134-禁中介",
        message_time="2026-05-06 15:33",
        sender_alias="鱼",
        body=body,
    )

    assert listing is not None
    assert listing["district_name"] == "荔湾区"
    assert "不短租" in listing["rental_tags"]
    assert "可短租" not in listing["rental_tags"]
    assert listing["rent_min"] == 750
    assert listing["rent_max"] == 1300


def test_extract_listing_rejects_text_without_rent():
    listing = extract_listing(
        source_file="sample.txt",
        source_group="广州租房群A134-禁中介",
        message_time="2026-05-06 16:12",
        sender_alias="小师妹",
        body="看到自己附近的房东，直接加房东微信，地铁30分钟左右可以到达的地方，都是优选！",
    )

    assert listing is None
