# 数据库 Schema 知识库

数据库名：`least`，共 29 张表。所有查询必须添加 `is_deleted = 0` 过滤条件。

## 核心业务表

### apartment_info 公寓信息表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 公寓 ID，主键 |
| name | varchar(64) | 公寓名称 |
| introduction | varchar(255) | 公寓介绍 |
| province_id | bigint | 省份 ID |
| province_name | varchar(16) | 省份名称（冗余） |
| city_id | bigint | 城市 ID |
| city_name | varchar(16) | 城市名称（冗余） |
| district_id | bigint | 区县 ID |
| district_name | varchar(16) | 区县名称（冗余） |
| address_detail | varchar(255) | 详细地址 |
| latitude | varchar(16) | 纬度 |
| longitude | varchar(16) | 经度 |
| phone | varchar(11) | 前台电话（敏感，脱敏返回） |
| is_release | tinyint | 是否发布：1=已发布，0=未发布 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

### room_info 房间信息表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 房间 ID，主键 |
| room_number | varchar(16) | 房间号 |
| rent | decimal(16,2) | 月租金（元） |
| apartment_id | bigint | 所属公寓 ID |
| is_release | tinyint | 是否发布：1=已发布，0=未发布 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

### view_appointment 预约看房表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 预约 ID，主键 |
| user_id | bigint | 用户 ID |
| name | varchar(16) | 用户姓名 |
| phone | varchar(16) | 用户手机号（敏感，脱敏返回） |
| apartment_id | int | 预约公寓 ID（注意：没有 room_id） |
| appointment_time | timestamp | 预约时间 |
| appointment_status | tinyint | 预约状态：1=待看房，2=已取消，3=已看房 |
| additional_info | varchar(255) | 备注 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

注意：预约表只有 apartment_id，没有 room_id，不能做房间维度预约分析。

### tenant_review 租客评价表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 评价 ID，主键 |
| user_id | bigint | 评价用户 ID |
| apartment_id | bigint | 公寓 ID |
| room_id | bigint | 房间 ID |
| rating | tinyint | 评分：1-5 星 |
| content | varchar(500) | 评价内容 |
| create_time | timestamp | 评价时间 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

### lease_agreement 租约信息表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 租约 ID，主键 |
| phone | varchar(11) | 承租人手机号（敏感，脱敏返回） |
| name | varchar(50) | 承租人姓名 |
| identification_number | varchar(18) | 身份证号（严禁返回） |
| apartment_id | bigint | 签约公寓 ID |
| room_id | bigint | 签约房间 ID |
| lease_start_date | date | 租约开始日期 |
| lease_end_date | date | 租约结束日期 |
| lease_term_id | bigint | 租期 ID |
| rent | decimal(16,2) | 月租金（元） |
| deposit | decimal(16,2) | 押金 |
| payment_type_id | bigint | 支付方式 ID |
| status | tinyint | 租约状态：1=签约待确认，2=已签约，3=已取消，4=已到期，5=退租待确认，6=已退租，7=续约待确认 |
| source_type | tinyint | 来源：1=新签，2=续约 |
| additional_info | varchar(255) | 备注 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

### browsing_history 浏览历史表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 浏览记录 ID，主键 |
| user_id | bigint | 用户 ID |
| room_id | bigint | 浏览房间 ID |
| browse_time | timestamp | 浏览时间 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

## 用户表

### user_info 移动端用户表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 用户 ID，主键 |
| phone | varchar(11) | 手机号（敏感，脱敏返回） |
| password | varchar(50) | 密码（严禁返回） |
| avatar_url | varchar(255) | 头像 |
| nickname | varchar(20) | 昵称 |
| status | tinyint | 账号状态：1=正常，0=禁用 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

### system_user 后台员工表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 员工 ID，主键 |
| username | varchar(30) | 登录用户名 |
| password | varchar(100) | 密码（严禁返回） |
| name | varchar(50) | 姓名 |
| type | tinyint | 类型：0=管理员，1=普通用户 |
| phone | varchar(11) | 手机号（敏感） |
| post_id | bigint | 岗位 ID |
| status | tinyint | 账号状态：1=正常，0=禁用 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

### system_post 岗位表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 岗位 ID，主键 |
| code | varchar(64) | 岗位编码 |
| name | varchar(50) | 岗位名称 |
| description | varchar(255) | 岗位描述 |
| status | tinyint | 状态：1=正常，0=禁用 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

## 地区表

### province_info 省份表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 省份 ID，主键 |
| name | varchar(16) | 省份名称 |

### city_info 城市表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | int | 城市 ID，主键 |
| name | varchar(16) | 城市名称 |
| province_id | int | 所属省份 ID |

### district_info 区县表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | int | 区县 ID，主键 |
| name | varchar(255) | 区县名称 |
| city_id | int | 所属城市 ID |

注意：公寓表已冗余了 province_name、city_name、district_name，常规分析直接用公寓表字段即可。

## 配置字典表

### lease_term 租期表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 租期 ID，主键 |
| month_count | int | 租期月数 |
| unit | varchar(16) | 单位 |

当前数据：1月、3月、6月、12月。

### payment_type 支付方式表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 支付方式 ID，主键 |
| name | varchar(16) | 名称 |
| pay_month_count | int | 每次支付月数 |
| additional_info | varchar(255) | 说明 |

当前数据：月付(1)、季付(3)、半年付(6)、年付(24)。

### label_info 标签表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 标签 ID，主键 |
| type | tinyint | 类型：1=公寓标签，2=房间标签 |
| name | varchar(255) | 标签名称 |

当前数据：近地铁、近公交、有电梯、停车场（公寓）；朝南、朝北、朝东、朝西、独卫、阳台（房间）。

### facility_info 配套设施表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 配套 ID，主键 |
| type | tinyint | 类型：1=公寓配套，2=房间配套 |
| name | varchar(16) | 配套名称 |
| icon | varchar(64) | 图标 |

当前数据：健身房、停车位、电梯、台球、安保、书吧等（公寓）；空调、洗衣机、冰箱、书桌、WIFI、床、沙发等（房间）。

### attr_key / attr_value 房间属性

attr_key（属性名）：id、name。
attr_value（属性值）：id、name、attr_key_id。

### fee_key / fee_value 杂费

fee_key（杂费名）：id、name。
fee_value（杂费值）：id、name、unit、fee_key_id。

## 关系表

| 表 | 作用 | 关联字段 |
|---|---|---|
| apartment_facility | 公寓-配套 | apartment_id, facility_id |
| apartment_label | 公寓-标签 | apartment_id, label_id |
| apartment_fee_value | 公寓-杂费 | apartment_id, fee_value_id |
| room_facility | 房间-配套 | room_id, facility_id |
| room_label | 房间-标签 | room_id, label_id |
| room_attr_value | 房间-属性值 | room_id, attr_value_id |
| room_lease_term | 房间-租期 | room_id, lease_term_id |
| room_payment_type | 房间-支付方式 | room_id, payment_type_id |

## 图片表

### graph_info 图片表

| 字段 | 类型 | 含义 |
|---|---|---|
| id | bigint | 图片 ID，主键 |
| name | varchar(128) | 图片名称 |
| item_type | tinyint | 关联类型：1=公寓，2=房间 |
| item_id | bigint | 关联 ID |
| url | varchar(255) | 图片地址 |
| is_deleted | tinyint | 逻辑删除：0=未删除 |

## 常用表关联

```
apartment_info.id = room_info.apartment_id
apartment_info.id = view_appointment.apartment_id
apartment_info.id = lease_agreement.apartment_id
room_info.id = lease_agreement.room_id
room_info.id = browsing_history.room_id
user_info.id = view_appointment.user_id
user_info.id = browsing_history.user_id
user_info.id = tenant_review.user_id
lease_term.id = lease_agreement.lease_term_id
payment_type.id = lease_agreement.payment_type_id
```

## 敏感字段（禁止直接返回）

- password（user_info、system_user）
- identification_number（lease_agreement）
- phone（user_info、system_user、view_appointment、lease_agreement、apartment_info）

如需返回手机号，必须使用脱敏：`CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS phone_masked`
