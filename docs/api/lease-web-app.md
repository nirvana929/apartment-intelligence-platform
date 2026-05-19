# lease web-app API 文档

**服务**: lease web-app
**端口**: 8081
**技术栈**: Spring Boot 3, Java 17, MyBatis-Plus
**数据库**: MySQL `least`

## 租户端 API (/app/*)

认证: JWT Token (通过 SMS 登录获取)

### 登录

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/app/login` | SMS 登录 |
| GET | `/app/login/getCode` | 发送验证码 |
| GET | `/app/info` | 获取当前用户信息 |

### 房源

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/app/room/pageItem` | 房间分页列表 |
| GET | `/app/room/getDetailById?id={id}` | 房间详情 |
| GET | `/app/room/pageItemByApartmentId` | 按公寓查房间 |

### 公寓

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/app/apartment/getDetailById?id={id}` | 公寓详情 |

### 预约

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/app/appointment/saveOrUpdate` | 创建/更新预约 |
| GET | `/app/appointment/listItem` | 我的预约列表 |
| GET | `/app/appointment/getDetailById?id={id}` | 预约详情 |

### 租约

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/app/agreement/listItem` | 我的租约列表 |
| GET | `/app/agreement/getDetailById?id={id}` | 租约详情 |
| POST | `/app/agreement/updateStatusById` | 更新租约状态 |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/app/history/pageItem` | 浏览历史 |
| GET | `/app/region/*` | 省/市/区查询 |
| GET | `/app/term/listByRoomId?roomId={id}` | 房间可选租期 |
| GET | `/app/payment/listByRoomId?roomId={id}` | 房间付款方式 |

### AI 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/app/ai/chat` | AI 对话 (转发到 AptGuide) |

---

## AI 工具接口 (/internal/ai/tools/*)

认证: `X-Internal-Token: aptguide-internal-token-2026`
用户标识: `X-User-Id` (部分接口可选)

### 房源搜索

```
POST /internal/ai/tools/room/search
Content-Type: application/json
X-Internal-Token: aptguide-internal-token-2026

{
  "roomIds": [2, 3, 10],       // 可选，房间 ID 列表
  "districtId": 1,              // 可选，区域 ID
  "maxRent": 2000,              // 可选，最高租金
  "minRent": 500,               // 可选，最低租金
  "paymentType": "月付",        // 可选，付款方式
  "leaseTermMonths": 12,        // 可选，租期月数
  "tags": ["近地铁"],           // 可选，标签
  "limit": 10                   // 可选，返回数量
}

Response:
{
  "code": 200,
  "message": "成功",
  "data": {
    "rooms": [
      {
        "roomId": 2,
        "roomNumber": "101",
        "apartmentId": 9,
        "apartmentName": "xxx公寓",
        "rent": 1500,
        "paymentTypes": ["月付"],
        "leaseTerms": [6, 12],
        "tags": ["近地铁"],
        "isAppointable": true
      }
    ],
    "total": 1
  }
}
```

### 房间同步

```
GET /internal/ai/tools/sync/rooms
X-Internal-Token: aptguide-internal-token-2026

Response: 房间列表 (用于同步到 Milvus)
```

### 健康检查

```
GET /internal/ai/tools/health
X-Internal-Token: aptguide-internal-token-2026

Response: {"code": 200, "message": "成功", "data": "ok"}
```

### 预约管理

```
POST /internal/ai/tools/appointment/create
X-Internal-Token: aptguide-internal-token-2026
X-User-Id: 1                    // 必填

{
  "apartmentId": 9,
  "appointmentTime": "2026-05-20 14:00",
  "remark": "想看两居室"
}

GET /internal/ai/tools/appointment/list-mine
X-Internal-Token: aptguide-internal-token-2026
X-User-Id: 1                    // 必填
```

### 租约查询

```
GET /internal/ai/tools/lease/list-mine
X-Internal-Token: aptguide-internal-token-2026
X-User-Id: 1                    // 必填
```

## OpenAPI 文档

lease web-app 内置 Swagger/OpenAPI 文档:

```
GET http://localhost:8081/v3/api-docs     # JSON 格式
GET http://localhost:8081/doc.html         # Knife4j UI (如果配置了)
```

## 已知问题

1. `room/search` 的 `roomIds` 必须使用 camelCase (Java DTO 要求)
2. Redis 连接失败会导致所有请求返回 `{"code":201,"message":"失败"}`
3. `room/search` 返回空可能是 roomIds 在数据库中不存在
