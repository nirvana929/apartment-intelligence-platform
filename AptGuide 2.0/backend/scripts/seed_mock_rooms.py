"""Seed mock room vectors into Milvus for testing.

Room IDs match the eval dataset (rag_mvp_retrieval_cases.yaml) expectations:
- IDs 1-20: budget rooms (800-2000), mostly 番禺/天河
- IDs 20-30: mid-range (2000-3000), 天河/海珠
- IDs 25, 32, 36: two-bedroom
- IDs 30-48: 海珠/越秀 area rooms
- IDs 200001-200060: "种子公寓" branded rooms
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.rag.chunking import build_room_vector_record
from aptguide2.tools.vector_adapter import VectorAdapter


MOCK_ROOMS = [
    # ===== Budget rooms (番禺区, district_id=1005) =====
    # id=1: cheap, 番禺, 单间
    {"room_id": 1, "apartment_id": 10, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "101", "apartment_name": "南亭寓", "rent": 800, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["便宜", "安静", "适合考研"], "facilities": ["空调", "WIFI", "床", "热水器"], "layout": "1室1卫", "area": 15},
    # id=2: cheap, 番禺
    {"room_id": 2, "apartment_id": 10, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "102", "apartment_name": "南亭寓", "rent": 900, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["便宜", "近地铁"], "facilities": ["空调", "WIFI", "床", "热水器"], "layout": "1室1卫", "area": 16},
    # id=3: cheap, 番禺, 合租
    {"room_id": 3, "apartment_id": 10, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城附近", "room_number": "A", "apartment_name": "大学城合租", "rent": 500, "payment_types": ["MONTHLY"], "lease_terms": [3, 6], "tags": ["合租", "便宜", "适合学生"], "facilities": ["WIFI", "床", "公共洗衣机"], "layout": "1室", "area": 10},
    # id=4: cheap, 番禺, 市桥
    {"room_id": 4, "apartment_id": 11, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "市桥附近", "room_number": "201", "apartment_name": "市桥公寓", "rent": 750, "payment_types": ["MONTHLY"], "lease_terms": [3, 6], "tags": ["便宜", "近地铁"], "facilities": ["WIFI", "床", "热水器"], "layout": "1室", "area": 12},
    # id=5: budget, 番禺, 独卫
    {"room_id": 5, "apartment_id": 11, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "市桥附近", "room_number": "301", "apartment_name": "市桥公寓", "rent": 1200, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["独卫", "近地铁", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 20},
    # id=6: budget, 番禺
    {"room_id": 6, "apartment_id": 12, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "番禺广场附近", "room_number": "401", "apartment_name": "番禺青年社区", "rent": 1100, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["安静", "配套齐全"], "facilities": ["空调", "热水器", "WIFI", "床", "洗衣机"], "layout": "1室1卫", "area": 18},
    # id=7: cheap, 番禺, 合租
    {"room_id": 7, "apartment_id": 12, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "番禺广场附近", "room_number": "B", "apartment_name": "番禺合租", "rent": 600, "payment_types": ["MONTHLY"], "lease_terms": [3, 6], "tags": ["合租", "便宜"], "facilities": ["WIFI", "床", "公共洗衣机"], "layout": "1室", "area": 10},
    # id=8: budget, 番禺, 近地铁, 采光好
    {"room_id": 8, "apartment_id": 13, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "市桥附近", "room_number": "501", "apartment_name": "市桥地铁公寓", "rent": 1300, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "配套齐全", "采光好"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 22},
    # id=9: budget, 番禺, 独卫
    {"room_id": 9, "apartment_id": 13, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "301", "apartment_name": "南亭独卫公寓", "rent": 1250, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["独卫", "安静", "适合考研"], "facilities": ["空调", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 20},
    # id=10: mid-budget, 番禺
    {"room_id": 10, "apartment_id": 14, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "501", "apartment_name": "南亭寓", "rent": 1500, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["安静", "采光好", "近大学城"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫"], "layout": "1室1卫", "area": 25},
    # id=11: budget, 番禺, 独卫
    {"room_id": 11, "apartment_id": 14, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城附近", "room_number": "402", "apartment_name": "南亭寓", "rent": 1180, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["独卫", "安静"], "facilities": ["空调", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 19},
    # id=12: mid-budget, 番禺
    {"room_id": 12, "apartment_id": 15, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "601", "apartment_name": "南亭阳光公寓", "rent": 1700, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["采光好", "朝南", "安静", "适合考研"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "阳台"], "layout": "1室1卫", "area": 26},
    # id=13: budget, 白云
    {"room_id": 13, "apartment_id": 16, "city_name": "广州", "district_name": "白云区", "district_id": 1006, "area_label": "白云大道附近", "room_number": "301", "apartment_name": "白云公寓", "rent": 900, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["便宜", "安静"], "facilities": ["空调", "热水器", "WIFI", "床"], "layout": "1室1卫", "area": 16},
    # id=14: mid-budget, 番禺, 近地铁
    {"room_id": 14, "apartment_id": 15, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "市桥附近", "room_number": "601", "apartment_name": "市桥地铁公寓", "rent": 1400, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "便宜"], "facilities": ["空调", "热水器", "WIFI", "床", "洗衣机"], "layout": "1室1卫", "area": 20},
    # id=15: budget, 番禺
    {"room_id": 15, "apartment_id": 17, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "番禺广场附近", "room_number": "201", "apartment_name": "番禺公寓", "rent": 1000, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["便宜", "配套齐全"], "facilities": ["空调", "热水器", "WIFI", "床"], "layout": "1室1卫", "area": 16},
    # id=16: mid-budget, 番禺
    {"room_id": 16, "apartment_id": 17, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "701", "apartment_name": "南亭寓", "rent": 1600, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["安静", "有阳台", "采光好"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "阳台"], "layout": "1室1卫", "area": 24},
    # id=17: budget, 白云
    {"room_id": 17, "apartment_id": 18, "city_name": "广州", "district_name": "白云区", "district_id": 1006, "area_label": "嘉禾望岗附近", "room_number": "401", "apartment_name": "嘉禾青年社区", "rent": 1100, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["近地铁", "便宜"], "facilities": ["空调", "热水器", "WIFI", "床", "洗衣机"], "layout": "1室1卫", "area": 18},
    # id=18: mid-budget, 番禺
    {"room_id": 18, "apartment_id": 18, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "801", "apartment_name": "南亭寓", "rent": 1800, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["安静", "适合考研", "独卫", "近地铁"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "阳台"], "layout": "1室1卫", "area": 30},
    # id=19: mid-budget, 海珠
    {"room_id": 19, "apartment_id": 19, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "江南西附近", "room_number": "301", "apartment_name": "江南西公寓", "rent": 1600, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["近地铁", "生活便利", "配套齐全"], "facilities": ["空调", "热水器", "WIFI", "床", "洗衣机"], "layout": "1室1卫", "area": 20},
    # id=20: mid-range, 天河
    {"room_id": 20, "apartment_id": 20, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "岗顶附近", "room_number": "601", "apartment_name": "岗顶白领公寓", "rent": 2200, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 22},
    # ===== Mid-range rooms (天河/海珠) =====
    # id=21
    {"room_id": 21, "apartment_id": 21, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "801", "apartment_name": "科韵白领公寓", "rent": 2500, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "衣柜", "电梯"], "layout": "1室1厅1卫", "area": 30},
    # id=22: mid-range, 天河
    {"room_id": 22, "apartment_id": 21, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "1001", "apartment_name": "科韵白领公寓", "rent": 2800, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["近地铁", "高楼层", "采光好", "新装修"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "衣柜", "电梯", "阳台"], "layout": "1室1厅1卫", "area": 35},
    # id=24
    {"room_id": 24, "apartment_id": 22, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "体育西附近", "room_number": "601", "apartment_name": "体育西公寓", "rent": 2600, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "繁华地段"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 24},
    # id=25: two-bedroom, 天河
    {"room_id": 25, "apartment_id": 23, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "701", "apartment_name": "科韵家庭公寓", "rent": 3500, "payment_types": ["QUARTERLY", "SEMI_ANNUAL"], "lease_terms": [12], "tags": ["两室", "适合家庭", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "厨房", "冰箱", "阳台", "电视"], "layout": "2室1厅1卫", "area": 55},
    # id=26
    {"room_id": 26, "apartment_id": 24, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "岗顶附近", "room_number": "401", "apartment_name": "岗顶公寓", "rent": 2400, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "配套齐全", "通勤方便"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "衣柜"], "layout": "1室1卫", "area": 22},
    # id=28
    {"room_id": 28, "apartment_id": 25, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "珠江新城附近", "room_number": "1501", "apartment_name": "珠江精品公寓", "rent": 3200, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["精装修", "高楼层", "视野好", "电梯"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "衣柜", "电梯", "阳台", "厨房"], "layout": "1室1厅1卫", "area": 40},
    # id=30
    {"room_id": 30, "apartment_id": 26, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "1201", "apartment_name": "科韵白领公寓", "rent": 3000, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["近地铁", "新装修", "高楼层"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "电梯", "阳台"], "layout": "1室1厅1卫", "area": 35},
    # id=32: two-bedroom
    {"room_id": 32, "apartment_id": 27, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "岗顶附近", "room_number": "901", "apartment_name": "岗顶家庭公寓", "rent": 3800, "payment_types": ["QUARTERLY", "SEMI_ANNUAL"], "lease_terms": [12], "tags": ["两室", "配套齐全", "近地铁"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "厨房", "阳台"], "layout": "2室1厅1卫", "area": 50},
    # ===== 海珠区 rooms =====
    # id=34
    {"room_id": 34, "apartment_id": 30, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "客村附近", "room_number": "701", "apartment_name": "客村青年社区", "rent": 1800, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "安静", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫"], "layout": "1室1卫", "area": 25},
    # id=35
    {"room_id": 35, "apartment_id": 30, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "客村附近", "room_number": "901", "apartment_name": "客村青年社区", "rent": 2200, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["近地铁", "采光好", "独卫"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "阳台"], "layout": "1室1卫", "area": 28},
    # id=36: two-bedroom, 海珠
    {"room_id": 36, "apartment_id": 31, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "琶洲附近", "room_number": "1101", "apartment_name": "琶洲家庭公寓", "rent": 3600, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["两室", "新装修", "电梯"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "厨房", "电梯", "阳台"], "layout": "2室1厅1卫", "area": 50},
    # id=38
    {"room_id": 38, "apartment_id": 31, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "琶洲附近", "room_number": "1301", "apartment_name": "琶洲公寓", "rent": 2600, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["新装修", "电梯", "近地铁"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "电梯", "阳台"], "layout": "1室1厅1卫", "area": 32},
    # id=40
    {"room_id": 40, "apartment_id": 32, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "江南西附近", "room_number": "501", "apartment_name": "江南西公寓", "rent": 1900, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "生活便利", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "衣柜"], "layout": "1室1卫", "area": 24},
    # id=42
    {"room_id": 42, "apartment_id": 32, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "江南西附近", "room_number": "801", "apartment_name": "江南西公寓", "rent": 2100, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["近地铁", "采光好", "高楼层"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "阳台"], "layout": "1室1卫", "area": 26},
    # ===== 越秀区 rooms =====
    # id=44
    {"room_id": 44, "apartment_id": 40, "city_name": "广州", "district_name": "越秀区", "district_id": 1002, "area_label": "北京路附近", "room_number": "501", "apartment_name": "北京路公寓", "rent": 2000, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "繁华地段", "生活便利"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 22},
    # id=46
    {"room_id": 46, "apartment_id": 40, "city_name": "广州", "district_name": "越秀区", "district_id": 1002, "area_label": "五羊邨附近", "room_number": "601", "apartment_name": "五羊公寓", "rent": 2300, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "安静", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫"], "layout": "1室1卫", "area": 24},
    # id=48
    {"room_id": 48, "apartment_id": 41, "city_name": "广州", "district_name": "越秀区", "district_id": 1002, "area_label": "五羊邨附近", "room_number": "801", "apartment_name": "五羊白领公寓", "rent": 2500, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["高楼层", "采光好", "近地铁"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "阳台"], "layout": "1室1卫", "area": 26},
    # ===== 种子公寓 rooms (200000 range) =====
    # id=200001: cheap, 种子公寓
    {"room_id": 200001, "apartment_id": 500, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "101", "apartment_name": "种子公寓南亭店", "rent": 850, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["便宜", "安静", "适合学生"], "facilities": ["空调", "WIFI", "床", "热水器"], "layout": "1室", "area": 14},
    # id=200002
    {"room_id": 200002, "apartment_id": 500, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "102", "apartment_name": "种子公寓南亭店", "rent": 950, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["便宜", "近地铁"], "facilities": ["空调", "WIFI", "床", "热水器"], "layout": "1室", "area": 15},
    # id=200003
    {"room_id": 200003, "apartment_id": 500, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城附近", "room_number": "201", "apartment_name": "种子公寓南亭店", "rent": 700, "payment_types": ["MONTHLY"], "lease_terms": [3, 6], "tags": ["合租", "便宜", "适合学生"], "facilities": ["WIFI", "床", "公共洗衣机"], "layout": "1室", "area": 10},
    # id=200005
    {"room_id": 200005, "apartment_id": 501, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "市桥附近", "room_number": "301", "apartment_name": "种子公寓市桥店", "rent": 1000, "payment_types": ["MONTHLY"], "lease_terms": [3, 6, 12], "tags": ["便宜", "近地铁", "配套齐全"], "facilities": ["空调", "热水器", "WIFI", "床", "洗衣机"], "layout": "1室1卫", "area": 18},
    # id=200008
    {"room_id": 200008, "apartment_id": 501, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "市桥附近", "room_number": "501", "apartment_name": "种子公寓市桥店", "rent": 1300, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 22},
    # id=200010
    {"room_id": 200010, "apartment_id": 502, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "401", "apartment_name": "种子公寓科韵店", "rent": 1500, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 22},
    # id=200012
    {"room_id": 200012, "apartment_id": 502, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "501", "apartment_name": "种子公寓科韵店", "rent": 1600, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["近地铁", "安静"], "facilities": ["空调", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 20},
    # id=200014
    {"room_id": 200014, "apartment_id": 503, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "601", "apartment_name": "种子公寓大学城店", "rent": 1400, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["安静", "适合考研", "近地铁"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫"], "layout": "1室1卫", "area": 24},
    # id=200015
    {"room_id": 200015, "apartment_id": 503, "city_name": "广州", "district_name": "番禺区", "district_id": 1005, "area_label": "大学城南亭附近", "room_number": "701", "apartment_name": "种子公寓大学城店", "rent": 1550, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["安静", "采光好", "独卫"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "阳台"], "layout": "1室1卫", "area": 25},
    # id=200018
    {"room_id": 200018, "apartment_id": 504, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "岗顶附近", "room_number": "601", "apartment_name": "种子公寓岗顶店", "rent": 1800, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 22},
    # id=200020
    {"room_id": 200020, "apartment_id": 504, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "岗顶附近", "room_number": "801", "apartment_name": "种子公寓岗顶店", "rent": 1500, "payment_types": ["MONTHLY"], "lease_terms": [6, 12], "tags": ["近地铁", "安静", "配套齐全"], "facilities": ["空调", "热水器", "WIFI", "床", "独卫"], "layout": "1室1卫", "area": 20},
    # id=200025
    {"room_id": 200025, "apartment_id": 505, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "客村附近", "room_number": "401", "apartment_name": "种子公寓客村店", "rent": 1700, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "交通便利"], "facilities": ["空调", "热水器", "WIFI", "床", "洗衣机"], "layout": "1室1卫", "area": 20},
    # id=200028
    {"room_id": 200028, "apartment_id": 505, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "客村附近", "room_number": "601", "apartment_name": "种子公寓客村店", "rent": 1900, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["近地铁", "采光好"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "阳台"], "layout": "1室1卫", "area": 24},
    # id=200030
    {"room_id": 200030, "apartment_id": 506, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "901", "apartment_name": "种子公寓科韵旗舰店", "rent": 1500, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "新装修", "配套齐全"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "电梯"], "layout": "1室1卫", "area": 22},
    # id=200035
    {"room_id": 200035, "apartment_id": 506, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "科韵路附近", "room_number": "1101", "apartment_name": "种子公寓科韵旗舰店", "rent": 2000, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["新装修", "高楼层", "电梯", "近地铁"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "电梯", "阳台"], "layout": "1室1卫", "area": 26},
    # id=200040
    {"room_id": 200040, "apartment_id": 507, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "体育西附近", "room_number": "701", "apartment_name": "种子公寓体育西店", "rent": 2500, "payment_types": ["MONTHLY", "QUARTERLY"], "lease_terms": [6, 12], "tags": ["近地铁", "通勤方便", "繁华地段"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "电梯"], "layout": "1室1卫", "area": 24},
    # id=200045
    {"room_id": 200045, "apartment_id": 507, "city_name": "广州", "district_name": "天河区", "district_id": 1001, "area_label": "体育西附近", "room_number": "901", "apartment_name": "种子公寓体育西店", "rent": 2800, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["近地铁", "高楼层", "采光好"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "电梯", "阳台"], "layout": "1室1卫", "area": 28},
    # id=200050
    {"room_id": 200050, "apartment_id": 508, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "琶洲附近", "room_number": "1201", "apartment_name": "种子公寓琶洲店", "rent": 2600, "payment_types": ["QUARTERLY"], "lease_terms": [12], "tags": ["新装修", "电梯", "近地铁", "高楼层"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "独卫", "电梯", "阳台"], "layout": "1室1厅1卫", "area": 30},
    # id=200060
    {"room_id": 200060, "apartment_id": 508, "city_name": "广州", "district_name": "海珠区", "district_id": 1003, "area_label": "琶洲附近", "room_number": "1501", "apartment_name": "种子公寓琶洲店", "rent": 3000, "payment_types": ["QUARTERLY", "SEMI_ANNUAL"], "lease_terms": [12], "tags": ["精装修", "高楼层", "视野好", "电梯", "新装修"], "facilities": ["空调", "洗衣机", "热水器", "WIFI", "床", "书桌", "独卫", "电梯", "阳台", "厨房", "冰箱"], "layout": "1室1厅1卫", "area": 38},
]


def embed_texts(texts: list[str], settings: Settings) -> list[list[float]]:
    """Embed texts using OpenAI-compatible API."""
    if not texts:
        return []
    client = OpenAI(
        api_key=settings.embedding_api_key.get_secret_value(),
        base_url=settings.embedding_base_url,
    )
    all_embeddings = []
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        all_embeddings.extend([d.embedding for d in response.data])
    return all_embeddings


def main():
    settings = Settings()

    adapter = VectorAdapter(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        dim=settings.embedding_dim,
    )
    adapter.ensure_room_collection()

    # Build vector records
    records = []
    for room in MOCK_ROOMS:
        record = build_room_vector_record(room, source_version=1)
        records.append(record)

    print(f"Built {len(records)} room vector records")

    # Embed
    texts = [r.content for r in records]
    print(f"Embedding {len(texts)} texts...")
    embeddings = embed_texts(texts, settings)
    print(f"Got {len(embeddings)} embeddings")

    # Upsert
    pairs = list(zip(records, embeddings))
    count = adapter.upsert_room_records(pairs)
    print(f"Upserted {count} room vectors to Milvus")

    # Verify
    client = adapter._ensure_client()
    client.load_collection("apt_room_vector")
    stats = client.query(
        collection_name="apt_room_vector",
        filter='status == "active"',
        output_fields=["room_id"],
    )
    print(f"Total active rooms in Milvus: {len(stats)}")


if __name__ == "__main__":
    main()
