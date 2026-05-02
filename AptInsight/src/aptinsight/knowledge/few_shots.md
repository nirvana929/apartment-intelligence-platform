# Few-shot 示例

以下是典型用户问题和对应的 SQL 查询示例。

## 示例 1：本月各公寓预约量排名

用户问题：本月各公寓预约量排名

```sql
SELECT
  ai.name AS apartment_name,
  COUNT(va.id) AS appointment_count
FROM view_appointment va
JOIN apartment_info ai ON va.apartment_id = ai.id
WHERE va.is_deleted = 0
  AND ai.is_deleted = 0
  AND DATE_FORMAT(va.appointment_time, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')
GROUP BY ai.id, ai.name
ORDER BY appointment_count DESC
LIMIT 10;
```

图表类型：柱状图。

## 示例 2：最近 30 天预约趋势

用户问题：最近 30 天预约趋势

```sql
SELECT
  DATE(va.appointment_time) AS appointment_date,
  COUNT(va.id) AS appointment_count
FROM view_appointment va
WHERE va.is_deleted = 0
  AND va.appointment_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(va.appointment_time)
ORDER BY appointment_date ASC
LIMIT 200;
```

图表类型：折线图。

## 示例 3：当前租约状态占比

用户问题：当前租约状态占比

```sql
SELECT
  CASE la.status
    WHEN 1 THEN '签约待确认'
    WHEN 2 THEN '已签约'
    WHEN 3 THEN '已取消'
    WHEN 4 THEN '已到期'
    WHEN 5 THEN '退租待确认'
    WHEN 6 THEN '已退租'
    WHEN 7 THEN '续约待确认'
    ELSE '未知'
  END AS lease_status,
  COUNT(la.id) AS agreement_count
FROM lease_agreement la
WHERE la.is_deleted = 0
GROUP BY la.status
ORDER BY agreement_count DESC
LIMIT 20;
```

图表类型：饼图。

## 示例 4：各区域平均租金

用户问题：各区域平均租金

```sql
SELECT
  ai.district_name AS district_name,
  ROUND(AVG(ri.rent), 2) AS avg_rent,
  COUNT(ri.id) AS room_count
FROM room_info ri
JOIN apartment_info ai ON ri.apartment_id = ai.id
WHERE ri.is_deleted = 0
  AND ai.is_deleted = 0
  AND ri.is_release = 1
GROUP BY ai.district_id, ai.district_name
ORDER BY avg_rent DESC
LIMIT 50;
```

图表类型：柱状图。

## 示例 5：已发布但没有有效租约的房间

用户问题：哪些已发布房间当前没有有效租约

```sql
SELECT
  ai.name AS apartment_name,
  ri.room_number AS room_number,
  ri.rent AS rent
FROM room_info ri
JOIN apartment_info ai ON ri.apartment_id = ai.id
LEFT JOIN lease_agreement la
  ON la.room_id = ri.id
  AND la.is_deleted = 0
  AND la.status = 2
  AND CURDATE() BETWEEN la.lease_start_date AND la.lease_end_date
WHERE ri.is_deleted = 0
  AND ai.is_deleted = 0
  AND ri.is_release = 1
  AND la.id IS NULL
ORDER BY ri.rent DESC
LIMIT 100;
```

图表类型：表格。

## 示例 6：最近 30 天浏览量最高的房间

用户问题：最近 30 天浏览量最高的房间

```sql
SELECT
  ai.name AS apartment_name,
  ri.room_number AS room_number,
  COUNT(bh.id) AS browse_count
FROM browsing_history bh
JOIN room_info ri ON bh.room_id = ri.id
JOIN apartment_info ai ON ri.apartment_id = ai.id
WHERE bh.is_deleted = 0
  AND ri.is_deleted = 0
  AND ai.is_deleted = 0
  AND bh.browse_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY ai.id, ai.name, ri.id, ri.room_number
ORDER BY browse_count DESC
LIMIT 10;
```

图表类型：柱状图。

## 示例 7：最近 6 个月新增租约趋势

用户问题：最近 6 个月新增租约趋势

```sql
SELECT
  DATE_FORMAT(la.create_time, '%Y-%m') AS month,
  COUNT(la.id) AS agreement_count
FROM lease_agreement la
WHERE la.is_deleted = 0
  AND la.create_time >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY DATE_FORMAT(la.create_time, '%Y-%m')
ORDER BY month ASC
LIMIT 12;
```

图表类型：折线图。

## 示例 8：预约量高但签约量低的公寓

用户问题：哪些公寓预约量高但签约量低

```sql
SELECT
  ai.name AS apartment_name,
  COUNT(DISTINCT va.id) AS appointment_count,
  COUNT(DISTINCT la.id) AS signed_count,
  ROUND(
    COUNT(DISTINCT la.id) / NULLIF(COUNT(DISTINCT va.id), 0),
    4
  ) AS reference_conversion_rate
FROM apartment_info ai
LEFT JOIN view_appointment va
  ON va.apartment_id = ai.id
  AND va.is_deleted = 0
  AND va.appointment_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
LEFT JOIN lease_agreement la
  ON la.apartment_id = ai.id
  AND la.is_deleted = 0
  AND la.status = 2
  AND la.create_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
WHERE ai.is_deleted = 0
GROUP BY ai.id, ai.name
HAVING appointment_count > 0
ORDER BY appointment_count DESC, reference_conversion_rate ASC
LIMIT 10;
```

图表类型：表格。

## 示例 9：不支持的问题

用户问题：预约量最高的房间有哪些？

回答策略：当前数据库的 view_appointment 表只有 apartment_id，没有 room_id，不能准确统计房间维度预约量。可以改为统计各公寓预约量排名。

不要生成错误 SQL。

## 示例 10：各公寓平均评分

用户问题：各公寓平均评分是多少

```sql
SELECT
  ai.name AS apartment_name,
  ROUND(AVG(tr.rating), 2) AS avg_rating,
  COUNT(tr.id) AS review_count
FROM tenant_review tr
JOIN apartment_info ai ON tr.apartment_id = ai.id
WHERE tr.is_deleted = 0
  AND ai.is_deleted = 0
GROUP BY ai.id, ai.name
ORDER BY avg_rating DESC
LIMIT 20;
```

图表类型：柱状图。

## 示例 11：低分评价内容

用户问题：评分最低的评价有哪些

```sql
SELECT
  ai.name AS apartment_name,
  ri.room_number,
  tr.rating,
  tr.content,
  tr.create_time
FROM tenant_review tr
JOIN apartment_info ai ON tr.apartment_id = ai.id
JOIN room_info ri ON tr.room_id = ri.id
WHERE tr.is_deleted = 0
  AND ai.is_deleted = 0
  AND ri.is_deleted = 0
  AND tr.rating <= 2
ORDER BY tr.rating ASC, tr.create_time DESC
LIMIT 20;
```

图表类型：表格。
