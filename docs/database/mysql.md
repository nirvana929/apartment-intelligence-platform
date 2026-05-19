# MySQL 数据库文档

## 概览

平台共有 4 个 MySQL 数据库，运行在同一个 MySQL 8.0 实例上（端口 3306）。

## 连接信息

| 项目 | 用户 | 密码 | 主机 | 数据库名 |
|------|------|------|------|----------|
| lease web-app | chove | 123456 | 127.0.0.1:3306 | least |
| lease web-admin | chove | 123456 | 127.0.0.1:3306 | lease |
| AptGuide 2.0 | root | change-me | localhost:3306 | aptguide2 |
| AptGuide 3.0 | root | change-me | localhost:3306 | aptguide3 |
| AptInsight | chove | 123456 | 192.168.211.128:3306 | least (只读) |

> **注意**: lease web-app 和 web-admin 使用不同的数据库名 (`least` vs `lease`)，这是历史遗留问题。

## 数据库: `least` (lease 业务主库)

这是平台的核心业务数据库，存储所有公寓、房间、预约、租约、用户数据。

### 微信房源表

| 表名 | 用途 | 主要字段 |
|------|------|----------|
| `wechat_listings` | 微信群提取的房源 | id, district_name, area_label, rent_min, rent_max, layouts(JSON), metro_stations(JSON), facility_tags(JSON), payment_tags(JSON), rental_tags(JSON), description_sanitized, message_time, source_group |

数据来源: `AptGuide/data/wechat_rental_listings_sanitized.jsonl`
当前数据量: 44 条
Milvus 对应 Collection: `wechat_room_index`

### 核心表

| 表名 | 用途 | 主要字段 |
|------|------|----------|
| `apartment_info` | 公寓信息 | id, name, introduction, district_id, address, longitude, latitude, phone |
| `room_info` | 房间信息 | id, apartment_id, room_number, rent, payment_type_id, lease_term_id, status |
| `district_info` | 区域信息 | id, name, city_id |
| `city_info` | 城市信息 | id, name, province_id |
| `province_info` | 省份信息 | id, name |
| `user_info` | 用户信息 | id, phone, name, avatar_url, id_card |
| `view_appointment` | 看房预约 | id, user_id, apartment_id, appointment_time, status, remark |
| `lease_agreement` | 租约合同 | id, user_id, room_id, apartment_id, start_date, end_date, rent, status |
| `payment_type` | 付款方式 | id, name (月付/季付/半年付/年付) |
| `lease_term` | 租期选项 | id, month_count |
| `room_payment_type` | 房间-付款方式关联 | room_id, payment_type_id |
| `room_lease_term` | 房间-租期关联 | room_id, lease_term_id |
| `facility_info` | 设施信息 | id, name, type (配套设施/配套家电) |
| `apartment_facility` | 公寓-设施关联 | apartment_id, facility_id |
| `fee_key` | 费用项目 | id, name |
| `fee_value` | 费用值 | id, fee_key_id, value |
| `apartment_fee_value` | 公寓-费用关联 | apartment_id, fee_value_id |
| `attr_key` | 属性项目 | id, name, type |
| `attr_value` | 属性值 | id, attr_key_id, value |
| `room_attr_value` | 房间-属性关联 | room_id, attr_value_id |
| `label` | 标签 | id, name, type |
| `room_label` | 房间-标签关联 | room_id, label_id |
| `graph_info` | 图片信息 | id, graph_type, graph_url, apartment_id, room_id |
| `browsing_history` | 浏览历史 | id, user_id, room_id |

### Room ID 范围

当前 `room_info` 表中的 ID 范围: **2 ~ 38+** (小数字 ID)

> **关键发现**: Milvus `room_index` 中的 room_id (3001-3102) 与此表的 ID 不一致。详见 [data-sync.md](data-sync.md)。

## 数据库: `lease` (lease 管理后台)

与 `least` 结构相同，用于 web-admin 管理后台。生产环境应统一为同一个库。

## 数据库: `aptguide2` (AptGuide 2.0 Agent 状态)

AptGuide 2.0 的 Agent 运行时状态存储。

| 表名 | 用途 |
|------|------|
| `sessions` | 会话记录 |
| `messages` | 消息历史 |
| `pending_actions` | 待确认操作 |

## 数据库: `aptguide3` (AptGuide 3.0 Agent 状态)

AptGuide 3.0 的完整 Agent 状态存储，共 11 张表。

| 表名 | 用途 |
|------|------|
| `aptguide3_users` | 用户信息 |
| `aptguide3_sessions` | 会话记录 |
| `aptguide3_messages` | 消息历史 |
| `aptguide3_pending_actions` | 待确认操作 (有 TTL) |
| `aptguide3_memories` | 长期记忆 |
| `aptguide3_memory_candidates` | 记忆候选 |
| `aptguide3_handoff_tickets` | 人工转接工单 |
| `aptguide3_operator_messages` | 运营商消息 |
| `aptguide3_trace_events` | 追踪事件 |
| `aptguide3_procedure_runs` | 过程执行记录 |
| `aptguide3_audit_log` | 审计日志 |

Schema 定义: `AptGuide 3.0/backend/src/aptguide3/database/schema.sql`

## 数据关系图

```
province_info
  └── city_info
        └── district_info
              └── apartment_info
                    ├── room_info
                    │     ├── room_payment_type → payment_type
                    │     ├── room_lease_term → lease_term
                    │     ├── room_attr_value → attr_value → attr_key
                    │     ├── room_label → label
                    │     ├── graph_info (room photos)
                    │     └── browsing_history ← user_info
                    ├── apartment_facility → facility_info
                    ├── apartment_fee_value → fee_value → fee_key
                    ├── graph_info (apartment photos)
                    └── view_appointment ← user_info
                          └── lease_agreement ← user_info, room_info
```
