from aptguide2.data_import.wechat_local_mysql_parser import (
    extract_contacts,
    extract_listing,
    parse_message_blocks,
)


def test_parse_message_blocks_keeps_sender_and_text_body():
    text = """群名: 广州租房群A134-禁中介

[2026-05-06 15:43] 广州房东直租 (text): 🏠 天河棠下-上社房东自建屋
单间680-950
电话同步18620724159
---"""

    blocks = parse_message_blocks(text, "sample.txt")

    assert len(blocks) == 1
    assert blocks[0].message_time == "2026-05-06 15:43"
    assert blocks[0].sender_alias == "广州房东直租"
    assert blocks[0].message_type == "text"
    assert "电话同步18620724159" in blocks[0].body


def test_extract_contacts_keeps_phone_numbers():
    contacts = extract_contacts("请加微信 18998438337微信，电话同步18620724159")

    assert sorted(contacts["phone_numbers"]) == ["18620724159", "18998438337"]
    assert "18998438337" in contacts["contact_text"]


def test_extract_listing_keeps_contact_fields():
    body = """天河黄村4/21珠村13号线三地铁线房东直租
✅ 步行6分钟到地铁
✅ 房东直租 无中介费
✅ 民水民电
✅ 押一付一
599起拿下阳光大单间
699起住一房一厅
联系方式：15202955805（微信同步）"""

    listing = extract_listing(
        source_file="sample.txt",
        source_group="广州租房群A134-禁中介",
        message_time="2026-04-30 06:34",
        sender_alias="爱杰的可可",
        message_type="text",
        body=body,
    )

    assert listing is not None
    assert listing["source_type"] == "WECHAT_GROUP"
    assert listing["authenticity"] == "REAL_POSTED"
    assert listing["verification_status"] == "UNVERIFIED"
    assert listing["availability_status"] == "UNKNOWN"
    assert listing["district_name"] == "天河区"
    assert listing["rent_min"] == 599
    assert listing["rent_max"] == 699
    assert listing["phone_numbers"] == ["15202955805"]
    assert "15202955805" in listing["contact_text"]
    assert "15202955805" in listing["raw_text"]
    assert listing["is_active"] is True
    assert listing["appointable"] is False


def test_extract_listing_rejects_text_without_rent():
    listing = extract_listing(
        source_file="sample.txt",
        source_group="广州租房群A134-禁中介",
        message_time="2026-05-06 16:12",
        sender_alias="小师妹",
        message_type="text",
        body="看到自己附近的房东，直接加房东微信，地铁30分钟左右可以到达的地方，都是优选！",
    )

    assert listing is None
