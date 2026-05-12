# 业务指标定义

## 预约类指标

### 预约量
定义：view_appointment 中未删除的预约记录数。
SQL：`COUNT(id) WHERE is_deleted = 0`

按状态拆分：
- 待看房：`appointment_status = 1`
- 已取消：`appointment_status = 2`
- 已看房：`appointment_status = 3`

### 看房完成率
定义：已看房预约量 / 总预约量。
公式：`COUNT(appointment_status = 3) / COUNT(appointment_status IN (1,2,3))`

### 预约趋势
按 appointment_time 的日期或月份聚合，展示预约量变化。

## 租约类指标

### 签约量
定义：lease_agreement 中 status = 2 的记录数。
注意：status = 1 是"签约待确认"，不算已签约。

### 有效租约
定义：已签约且当前日期在租约起止日期之间。
条件：`status = 2 AND CURDATE() BETWEEN lease_start_date AND lease_end_date`

### 退租量
定义：`status = 6` 的记录数。

### 续约待确认量
定义：`status = 7` 的记录数。

### 租约状态分布
按 status 分组统计各状态数量，用 CASE WHEN 转中文名称。

### 租约来源分布
按 source_type 分组：1=新签，2=续约。

### 合同月租金规模
定义：已签约租约的 rent 合计。
公式：`SUM(rent) WHERE status = 2`
注意：这是合同口径，不是实际收款。当前没有账单表，不能计算真实收入。

## 房源类指标

### 房间数量
按公寓统计：`COUNT(room_info.id) WHERE is_deleted = 0`

### 已发布房间数
条件：`is_release = 1 AND is_deleted = 0`

### 空置房间
定义：已发布房间，当前没有有效租约。
逻辑：`room_info.is_release = 1` LEFT JOIN 有效租约，WHERE 有效租约 IS NULL。

### 租金区间分布
将 rent 按区间分组（如 0-1000、1000-2000、2000-3000 等），统计各区间房间数。

## 租金类指标

### 平均租金
公式：`AVG(room_info.rent)`，默认统计已发布未删除房间。

### 各公寓平均租金
按公寓分组计算 AVG(rent)。

### 各区域平均租金
按 district_name 分组计算 AVG(rent)。

## 浏览热度指标

### 浏览量
定义：browsing_history 中未删除记录数。

### 独立浏览用户数
公式：`COUNT(DISTINCT user_id)`

### 房间热度排名
按房间分组统计浏览量，取 TOP N。

### 浏览量高但未签约的房间
浏览量排名靠前，但 LEFT JOIN lease_agreement 找不到有效租约的房间。

## 经营诊断指标

### 预约转化率
定义：签约数 / 预约数。
注意：预约转化率的"预约"指 view_appointment 表的预约记录数，"签约"指 lease_agreement 中 status = 2 的已签约记录数。不要理解为"看房完成率"（那是已看房 / 总预约）。
公式：`COUNT(lease_agreement.status = 2) / COUNT(view_appointment.id WHERE is_deleted = 0)`
仅作参考，非精确转化链路（预约和租约无关联 ID）。

### 预约量高但签约量低的公寓
按公寓统计近 30 天预约量和签约量，计算参考转化率。
公式：签约数 / 预约数（仅作参考，非精确转化链路）。

### 空置风险房间
已发布房间中，长期没有有效租约的房间。

## 评价类指标

### 平均评分
公式：`AVG(tenant_review.rent)`，默认统计未删除评价。

### 各公寓平均评分
按公寓分组计算 AVG(rating)。

### 各房间平均评分
按房间分组计算 AVG(rating)。

### 低分评价
定义：rating <= 2 的评价。

### 评价趋势
按 create_time 的日期或月份聚合，展示评价数量变化。

## 数据限制

以下指标当前数据库不支持：
- 真实收款收入（无账单/支付流水表）
- 房间维度预约量（view_appointment 无 room_id）
- 客户精确转化率（预约和租约无关联 ID）
