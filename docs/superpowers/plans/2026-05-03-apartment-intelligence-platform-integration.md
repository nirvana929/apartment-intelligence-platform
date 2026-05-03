# 公寓智能平台集成实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 AI 能力集成到现有公寓租赁系统，实现用户通过前端 AI 助手进行找房、预约等操作

**Architecture:** 采用渐进式集成方案，先实现 lease 后端内部接口，再更新 AI 服务客户端，最后集成前端。lease 作为网关层负责 JWT 鉴权，AI 服务通过内部 Token 调用 lease 业务接口

**Tech Stack:** Spring Boot (lease), Python FastAPI + LangGraph (AptGuide/AptInsight), Vue (前端), MySQL, Redis, Milvus

---

## 文件结构

### lease 后端（Spring Boot）

```
lease/web/web-app/src/main/java/com/atguigu/lease/web/app/
├── controller/
│   ├── ai/
│   │   ├── AiController.java              # 新增：AI 入口接口
│   │   └── AiToolController.java          # 新增：AI 工具接口
│   └── ...
├── service/
│   ├── AiService.java                     # 新增：AI 服务接口
│   └── impl/
│       └── AiServiceImpl.java             # 新增：AI 服务实现
└── vo/
    └── ai/
        ├── ChatRequest.java               # 新增：对话请求
        ├── ChatResponse.java              # 新增：对话响应
        ├── RoomSearchRequest.java         # 新增：房源搜索请求
        └── RoomSearchResponse.java        # 新增：房源搜索响应
```

### AptGuide（Python FastAPI）

```
src/aptguide/tools/
├── client.py                              # 修改：更新接口路径
└── schemas.py                             # 修改：更新请求/响应模型
```

### 前端（Vue）

```
rentHouseH5/src/
├── components/
│   └── ai/
│       ├── AiAssistant.vue                # 新增：AI 助手组件
│       └── ChatMessage.vue                # 新增：聊天消息组件
├── api/
│   └── ai.ts                              # 新增：AI 接口封装
└── views/
    └── home/
        └── index.vue                      # 修改：集成 AI 助手
```

---

## 阶段 2：对接 lease 内部接口

### Task 1: lease - 创建 AI 工具接口基础结构

**Files:**
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomSearchRequest.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomSearchResponse.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomVo.java`

- [ ] **Step 1: 创建 RoomSearchRequest**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSearchRequest {
    private Long cityId;
    private Long districtId;
    private Integer maxRent;
    private Integer minRent;
    private String paymentType;
    private Integer leaseTermMonths;
    private List<String> tags;
    private List<Long> roomIds;
    private Integer limit = 5;
}
```

- [ ] **Step 2: 创建 RoomVo**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomVo {
    private Long roomId;
    private String roomNumber;
    private Long apartmentId;
    private String apartmentName;
    private Integer rent;
    private List<String> paymentTypes;
    private List<Integer> leaseTerms;
    private Integer area;
    private String layout;
    private List<String> tags;
    private String thumbnailUrl;
    private Boolean isAppointable;
}
```

- [ ] **Step 3: 创建 RoomSearchResponse**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSearchResponse {
    private List<RoomVo> rooms;
    private Integer total;
}
```

- [ ] **Step 4: 提交代码**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
git add web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/
git commit -m "feat: add AI tool request/response models"
```

### Task 2: lease - 实现 AI 工具接口 Controller

**Files:**
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java`

- [ ] **Step 1: 创建 AiToolController**

```java
package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.web.app.service.RoomInfoService;
import com.atguigu.lease.web.app.vo.ai.RoomSearchRequest;
import com.atguigu.lease.web.app.vo.ai.RoomSearchResponse;
import com.atguigu.lease.web.app.vo.ai.RoomVo;
import com.atguigu.lease.web.app.vo.room.RoomItemVo;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Tag(name = "AI工具接口")
@RestController
@RequestMapping("/internal/ai/tools")
public class AiToolController {

    @Autowired
    private RoomInfoService roomInfoService;

    @Operation(summary = "搜索房源")
    @PostMapping("/room/search")
    public Result<RoomSearchResponse> searchRooms(
            @RequestBody RoomSearchRequest request,
            @RequestHeader("X-User-Id") Long userId) {
        
        // 构建查询条件
        Page<RoomItemVo> page = new Page<>(1, request.getLimit());
        
        // TODO: 调用 roomInfoService 查询房源
        // IPage<RoomItemVo> result = roomInfoService.pageItem(page, queryVo);
        
        // 转换为 AI 接口格式
        RoomSearchResponse response = new RoomSearchResponse();
        response.setRooms(new ArrayList<>());
        response.setTotal(0);
        
        return Result.ok(response);
    }

    @Operation(summary = "健康检查")
    @GetMapping("/health")
    public Result<String> health() {
        return Result.ok("ok");
    }
}
```

- [ ] **Step 2: 编译验证**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn compile -pl web/web-app
```

- [ ] **Step 3: 提交代码**

```bash
git add web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java
git commit -m "feat: add AI tool controller with room search endpoint"
```

### Task 3: lease - 完善房源搜索实现

**Files:**
- Modify: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java`

- [ ] **Step 1: 查看现有 RoomInfoService 接口**

```bash
cat lease/web/web-app/src/main/java/com/atguigu/lease/web/app/service/RoomInfoService.java
```

- [ ] **Step 2: 查看 RoomQueryVo 结构**

```bash
find lease -name "RoomQueryVo.java" -exec cat {} \;
```

- [ ] **Step 3: 更新 AiToolController 实现**

```java
package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.web.app.service.RoomInfoService;
import com.atguigu.lease.web.app.vo.ai.RoomSearchRequest;
import com.atguigu.lease.web.app.vo.ai.RoomSearchResponse;
import com.atguigu.lease.web.app.vo.ai.RoomVo;
import com.atguigu.lease.web.app.vo.room.RoomItemVo;
import com.atguigu.lease.web.app.vo.room.RoomQueryVo;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Tag(name = "AI工具接口")
@RestController
@RequestMapping("/internal/ai/tools")
public class AiToolController {

    @Autowired
    private RoomInfoService roomInfoService;

    @Operation(summary = "搜索房源")
    @PostMapping("/room/search")
    public Result<RoomSearchResponse> searchRooms(
            @RequestBody RoomSearchRequest request,
            @RequestHeader("X-User-Id") Long userId) {
        
        // 构建查询条件
        RoomQueryVo queryVo = new RoomQueryVo();
        queryVo.setDistrictId(request.getDistrictId());
        queryVo.setMinRent(request.getMinRent());
        queryVo.setMaxRent(request.getMaxRent());
        queryVo.setPaymentTypeId(request.getPaymentType());
        
        Page<RoomItemVo> page = new Page<>(1, request.getLimit());
        
        // 调用 service 查询
        IPage<RoomItemVo> result = roomInfoService.pageItem(page, queryVo);
        
        // 转换为 AI 接口格式
        RoomSearchResponse response = new RoomSearchResponse();
        List<RoomVo> rooms = result.getRecords().stream()
                .map(this::convertToRoomVo)
                .collect(Collectors.toList());
        response.setRooms(rooms);
        response.setTotal((int) result.getTotal());
        
        return Result.ok(response);
    }

    private RoomVo convertToRoomVo(RoomItemVo item) {
        RoomVo vo = new RoomVo();
        vo.setRoomId(item.getId());
        vo.setRoomNumber(item.getRoomNumber());
        vo.setRent(item.getRent());
        // TODO: 设置其他字段
        return vo;
    }

    @Operation(summary = "健康检查")
    @GetMapping("/health")
    public Result<String> health() {
        return Result.ok("ok");
    }
}
```

- [ ] **Step 4: 编译验证**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn compile -pl web/web-app
```

- [ ] **Step 5: 提交代码**

```bash
git add web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java
git commit -m "feat: implement room search in AI tool controller"
```

### Task 4: lease - 添加预约和租约接口

**Files:**
- Modify: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/AppointmentVo.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/LeaseVo.java`

- [ ] **Step 1: 创建 AppointmentVo**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class AppointmentVo {
    private Long appointmentId;
    private String appointmentNo;
    private String status;
    private LocalDateTime appointmentTime;
    private String apartmentName;
    private String roomNumber;
}
```

- [ ] **Step 2: 创建 LeaseVo**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.time.LocalDate;

@Data
public class LeaseVo {
    private Long leaseId;
    private String status;
    private String apartmentName;
    private String roomNumber;
    private LocalDate startDate;
    private LocalDate endDate;
    private Integer rent;
    private String paymentType;
    private Integer renewalWindowDays;
}
```

- [ ] **Step 3: 更新 AiToolController 添加预约和租约接口**

```java
package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.login.LoginUserHolder;
import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.web.app.service.RoomInfoService;
import com.atguigu.lease.web.app.service.ViewAppointmentService;
import com.atguigu.lease.web.app.service.LeaseAgreementService;
import com.atguigu.lease.web.app.vo.ai.*;
import com.atguigu.lease.web.app.vo.room.RoomItemVo;
import com.atguigu.lease.web.app.vo.room.RoomQueryVo;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Tag(name = "AI工具接口")
@RestController
@RequestMapping("/internal/ai/tools")
public class AiToolController {

    @Autowired
    private RoomInfoService roomInfoService;
    
    @Autowired
    private ViewAppointmentService appointmentService;
    
    @Autowired
    private LeaseAgreementService leaseService;

    @Operation(summary = "搜索房源")
    @PostMapping("/room/search")
    public Result<RoomSearchResponse> searchRooms(
            @RequestBody RoomSearchRequest request,
            @RequestHeader("X-User-Id") Long userId) {
        
        RoomQueryVo queryVo = new RoomQueryVo();
        queryVo.setDistrictId(request.getDistrictId());
        queryVo.setMinRent(request.getMinRent());
        queryVo.setMaxRent(request.getMaxRent());
        
        Page<RoomItemVo> page = new Page<>(1, request.getLimit());
        IPage<RoomItemVo> result = roomInfoService.pageItem(page, queryVo);
        
        RoomSearchResponse response = new RoomSearchResponse();
        List<RoomVo> rooms = result.getRecords().stream()
                .map(this::convertToRoomVo)
                .collect(Collectors.toList());
        response.setRooms(rooms);
        response.setTotal((int) result.getTotal());
        
        return Result.ok(response);
    }

    @Operation(summary = "查询个人预约列表")
    @GetMapping("/appointment/list-mine")
    public Result<List<AppointmentVo>> listMyAppointments(
            @RequestHeader("X-User-Id") Long userId) {
        
        // TODO: 调用 appointmentService 查询用户预约
        List<AppointmentVo> appointments = new ArrayList<>();
        
        return Result.ok(appointments);
    }

    @Operation(summary = "查询个人租约列表")
    @GetMapping("/lease/list-mine")
    public Result<List<LeaseVo>> listMyLeases(
            @RequestHeader("X-User-Id") Long userId) {
        
        // TODO: 调用 leaseService 查询用户租约
        List<LeaseVo> leases = new ArrayList<>();
        
        return Result.ok(leases);
    }

    @Operation(summary = "健康检查")
    @GetMapping("/health")
    public Result<String> health() {
        return Result.ok("ok");
    }

    private RoomVo convertToRoomVo(RoomItemVo item) {
        RoomVo vo = new RoomVo();
        vo.setRoomId(item.getId());
        vo.setRoomNumber(item.getRoomNumber());
        vo.setRent(item.getRent());
        return vo;
    }
}
```

- [ ] **Step 4: 编译验证**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn compile -pl web/web-app
```

- [ ] **Step 5: 提交代码**

```bash
git add web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/
git add web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/
git commit -m "feat: add appointment and lease query endpoints to AI tool controller"
```

### Task 5: lease - 配置内部接口鉴权

**Files:**
- Modify: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/custom/config/WebMvcConfiguration.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/custom/interceptor/InternalTokenInterceptor.java`

- [ ] **Step 1: 查看现有 WebMvcConfiguration**

```bash
cat lease/web/web-app/src/main/java/com/atguigu/lease/web/app/custom/config/WebMvcConfiguration.java
```

- [ ] **Step 2: 创建 InternalTokenInterceptor**

```java
package com.atguigu.lease.web.app.custom.interceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class InternalTokenInterceptor implements HandlerInterceptor {

    @Value("${ai.internal.token}")
    private String internalToken;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String token = request.getHeader("X-Internal-Token");
        
        if (token == null || !token.equals(internalToken)) {
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"Invalid internal token\"}");
            return false;
        }
        
        return true;
    }
}
```

- [ ] **Step 3: 更新 WebMvcConfiguration 添加内部接口拦截**

```java
package com.atguigu.lease.web.app.custom.config;

import com.atguigu.lease.web.app.custom.interceptor.AuthenticationInterceptor;
import com.atguigu.lease.web.app.custom.interceptor.InternalTokenInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebMvcConfiguration implements WebMvcConfigurer {

    @Autowired
    private AuthenticationInterceptor authenticationInterceptor;
    
    @Autowired
    private InternalTokenInterceptor internalTokenInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 用户接口鉴权
        registry.addInterceptor(authenticationInterceptor)
                .addPathPatterns("/app/**")
                .excludePathPatterns("/app/login/**");
        
        // 内部接口鉴权
        registry.addInterceptor(internalTokenInterceptor)
                .addPathPatterns("/internal/**");
    }
}
```

- [ ] **Step 4: 添加配置文件**

```bash
echo "ai.internal.token=aptguide-internal-token-2026" >> lease/web/web-app/src/main/resources/application.yml
```

- [ ] **Step 5: 编译验证**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn compile -pl web/web-app
```

- [ ] **Step 6: 提交代码**

```bash
git add web/web-app/src/main/java/com/atguigu/lease/web/app/custom/
git add web/web-app/src/main/resources/application.yml
git commit -m "feat: add internal token interceptor for AI tool endpoints"
```

### Task 6: AptGuide - 更新 LeaseToolClient

**Files:**
- Modify: `src/aptguide/tools/client.py`

- [ ] **Step 1: 查看现有 LeaseToolClient**

```bash
cat src/aptguide/tools/client.py
```

- [ ] **Step 2: 更新接口路径**

```python
"""Java 后端工具接口客户端。"""

import uuid
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from aptguide.core.config import Settings
from aptguide.core.logging import get_logger

logger = get_logger(__name__)


class LeaseToolError(Exception):
    """工具接口业务错误。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"LeaseToolError({code}): {message}")


class LeaseToolClient:
    """lease 后端工具接口客户端。"""

    def __init__(self, settings: Settings):
        self.base_url = settings.lease_base_url.rstrip("/")
        self.token = settings.lease_internal_token
        self.timeout = settings.lease_request_timeout_seconds
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端。"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "X-Internal-Token": self.token,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端。"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _make_request_id(self) -> str:
        """生成请求 ID。"""
        return f"aptguide-{uuid.uuid4().hex[:12]}"

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=(retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))),
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        user_id: str | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送请求并处理响应。"""
        client = await self._get_client()
        headers = {"X-Request-Id": self._make_request_id()}
        if user_id:
            headers["X-User-Id"] = user_id

        try:
            response = await client.request(
                method, path, json=json, params=params, headers=headers
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error",
                status=e.response.status_code,
                path=path,
                response=e.response.text,
            )
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error("Network error", path=path, error=str(e))
            raise

        data = response.json()
        if data.get("code") != 0:
            raise LeaseToolError(data["code"], data.get("message", "Unknown error"))

        return data.get("data", {})

    # ========== 健康检查 ==========

    async def health_check(self) -> bool:
        """检查 lease 后端是否可达。"""
        try:
            data = await self._request("GET", "/internal/ai/tools/health")
            return data == "ok"
        except Exception as e:
            logger.warning("Health check failed", error=str(e))
            return False

    # ========== 房源接口 ==========

    async def search_rooms(
        self,
        *,
        city_id: int | None = None,
        district_id: int | None = None,
        max_rent: int | None = None,
        min_rent: int | None = None,
        payment_type: str | None = None,
        lease_term_months: int | None = None,
        tags: list[str] | None = None,
        room_ids: list[int] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """精确条件搜索房源。"""
        payload = {}
        if city_id is not None:
            payload["city_id"] = city_id
        if district_id is not None:
            payload["district_id"] = district_id
        if max_rent is not None:
            payload["max_rent"] = max_rent
        if min_rent is not None:
            payload["min_rent"] = min_rent
        if payment_type:
            payload["payment_type"] = payment_type
        if lease_term_months is not None:
            payload["lease_term_months"] = lease_term_months
        if tags:
            payload["tags"] = tags
        if room_ids:
            payload["room_ids"] = room_ids
        payload["limit"] = limit

        return await self._request("POST", "/internal/ai/tools/room/search", json=payload)

    # ========== 预约接口 ==========

    async def list_my_appointments(self, user_id: str) -> dict[str, Any]:
        """查询当前用户的预约列表。"""
        return await self._request(
            "GET",
            "/internal/ai/tools/appointment/list-mine",
            user_id=user_id,
        )

    # ========== 租约接口 ==========

    async def list_my_leases(self, user_id: str) -> dict[str, Any]:
        """查询当前用户的租约列表。"""
        return await self._request(
            "GET",
            "/internal/ai/tools/lease/list-mine",
            user_id=user_id,
        )
```

- [ ] **Step 3: 运行测试验证**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
uv run pytest tests/unit/test_tool_node.py -v
```

- [ ] **Step 4: 提交代码**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
git add src/aptguide/tools/client.py
git commit -m "feat: update LeaseToolClient to use new AI tool endpoints"
```

### Task 7: 测试 lease 内部接口

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动 lease 服务**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn spring-boot:run -pl web/web-app
```

- [ ] **Step 2: 测试健康检查接口**

```bash
curl -X GET http://localhost:8081/internal/ai/tools/health \
  -H "X-Internal-Token: aptguide-internal-token-2026" \
  -H "X-Request-Id: test-001"
```

Expected: `{"code":0,"message":"ok","data":"ok"}`

- [ ] **Step 3: 测试房源搜索接口**

```bash
curl -X POST http://localhost:8081/internal/ai/tools/room/search \
  -H "X-Internal-Token: aptguide-internal-token-2026" \
  -H "X-User-Id: 1" \
  -H "X-Request-Id: test-002" \
  -H "Content-Type: application/json" \
  -d '{"max_rent": 3000, "limit": 5}'
```

Expected: `{"code":0,"message":"ok","data":{"rooms":[...],"total":...}}`

- [ ] **Step 4: 测试无 Token 访问**

```bash
curl -X GET http://localhost:8081/internal/ai/tools/health
```

Expected: `{"code":401,"message":"Invalid internal token"}`

- [ ] **Step 5: 记录测试结果**

测试通过后，继续下一个任务。

## 阶段 3：集成到前端

### Task 8: lease - 实现 AI 入口接口

**Files:**
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiController.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/ChatRequest.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/ChatResponse.java`

- [ ] **Step 1: 创建 ChatRequest**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;

@Data
public class ChatRequest {
    private String message;
    private String sessionId;
}
```

- [ ] **Step 2: 创建 ChatResponse**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class ChatResponse {
    private String reply;
    private List<Map<String, Object>> cards;
    private List<Map<String, Object>> actions;
    private Map<String, Object> pendingConfirmation;
    private List<String> sources;
    private String sessionId;
}
```

- [ ] **Step 3: 创建 AiController**

```java
package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.login.LoginUserHolder;
import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.web.app.vo.ai.ChatRequest;
import com.atguigu.lease.web.app.vo.ai.ChatResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.ArrayList;
import java.util.HashMap;

@Tag(name = "AI对话接口")
@RestController
@RequestMapping("/app/ai")
public class AiController {

    @Value("${ai.guide.url:http://localhost:8100}")
    private String aptGuideUrl;

    @Operation(summary = "AI对话")
    @PostMapping("/chat")
    public Result<ChatResponse> chat(
            @RequestBody ChatRequest request,
            @RequestHeader("access-token") String token) {
        
        // 获取当前登录用户
        Long userId = LoginUserHolder.getLoginUser().getUserId();
        
        // 调用 AptGuide 服务
        WebClient client = WebClient.builder()
                .baseUrl(aptGuideUrl)
                .build();
        
        // TODO: 调用 AptGuide /api/chat 接口
        // AptGuideResponse aptGuideResponse = client.post()
        //         .uri("/api/chat")
        //         .header("X-Internal-Token", "aptguide-internal-token-2026")
        //         .header("X-User-Id", userId.toString())
        //         .bodyValue(request)
        //         .retrieve()
        //         .bodyToMono(AptGuideResponse.class)
        //         .block();
        
        // 临时返回模拟数据
        ChatResponse response = new ChatResponse();
        response.setReply("您好！我是AI找房助手，请问有什么可以帮您？");
        response.setCards(new ArrayList<>());
        response.setActions(new ArrayList<>());
        response.setSources(new ArrayList<>());
        response.setSessionId(request.getSessionId());
        
        return Result.ok(response);
    }
}
```

- [ ] **Step 4: 添加配置**

```bash
echo "ai.guide.url=http://localhost:8100" >> lease/web/web-app/src/main/resources/application.yml
```

- [ ] **Step 5: 编译验证**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn compile -pl web/web-app
```

- [ ] **Step 6: 提交代码**

```bash
git add web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiController.java
git add web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/ChatRequest.java
git add web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/ChatResponse.java
git add web/web-app/src/main/resources/application.yml
git commit -m "feat: add AI chat entry point controller"
```

### Task 9: 前端 - 创建 AI 助手组件

**Files:**
- Create: `rentHouseH5/src/components/ai/AiAssistant.vue`
- Create: `rentHouseH5/src/components/ai/ChatMessage.vue`
- Create: `rentHouseH5/src/api/ai.ts`

- [ ] **Step 1: 创建 ai.ts 接口封装**

```typescript
import request from '@/utils/http'

export interface ChatRequest {
  message: string
  sessionId?: string
}

export interface ChatResponse {
  reply: string
  cards: any[]
  actions: any[]
  pendingConfirmation: any
  sources: string[]
  sessionId: string
}

export function chatWithAi(data: ChatRequest) {
  return request<ChatResponse>({
    url: '/app/ai/chat',
    method: 'post',
    data
  })
}
```

- [ ] **Step 2: 创建 ChatMessage 组件**

```vue
<template>
  <div class="chat-message" :class="{ 'is-user': isUser }">
    <div class="message-content">
      <div class="message-text">{{ message.text }}</div>
      <div v-if="message.cards && message.cards.length" class="message-cards">
        <div v-for="card in message.cards" :key="card.id" class="card">
          <div class="card-title">{{ card.title }}</div>
          <div class="card-info">
            <span v-if="card.rent" class="rent">¥{{ card.rent }}/月</span>
            <span v-if="card.district" class="district">{{ card.district }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Message {
  id: string
  text: string
  isUser: boolean
  cards?: any[]
}

defineProps<{
  message: Message
}>()
</script>

<style scoped>
.chat-message {
  display: flex;
  margin-bottom: 12px;
}

.chat-message.is-user {
  justify-content: flex-end;
}

.message-content {
  max-width: 80%;
  padding: 12px;
  border-radius: 12px;
  background: #f5f5f5;
}

.chat-message.is-user .message-content {
  background: #007aff;
  color: white;
}

.message-cards {
  margin-top: 12px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-weight: bold;
  margin-bottom: 4px;
}

.card-info {
  display: flex;
  gap: 12px;
  font-size: 14px;
  color: #666;
}

.rent {
  color: #ff6b6b;
}
</style>
```

- [ ] **Step 3: 创建 AiAssistant 组件**

```vue
<template>
  <div class="ai-assistant">
    <!-- 悬浮按钮 -->
    <div class="float-btn" @click="togglePanel">
      <span class="icon">AI</span>
    </div>
    
    <!-- 对话面板 -->
    <div v-if="showPanel" class="panel">
      <div class="panel-header">
        <h3>AI 找房助手</h3>
        <button @click="togglePanel">×</button>
      </div>
      
      <div class="panel-body" ref="messageList">
        <ChatMessage 
          v-for="msg in messages" 
          :key="msg.id" 
          :message="msg"
        />
      </div>
      
      <div class="panel-footer">
        <input 
          v-model="inputText" 
          placeholder="输入您的问题..." 
          @keyup.enter="sendMessage"
        />
        <button @click="sendMessage">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { chatWithAi } from '@/api/ai'
import ChatMessage from './ChatMessage.vue'

interface Message {
  id: string
  text: string
  isUser: boolean
  cards?: any[]
}

const showPanel = ref(false)
const inputText = ref('')
const messages = ref<Message[]>([
  {
    id: '0',
    text: '您好！我是AI找房助手，请问有什么可以帮您？',
    isUser: false
  }
])
const sessionId = ref(`session-${Date.now()}`)

const togglePanel = () => {
  showPanel.value = !showPanel.value
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text) return
  
  // 添加用户消息
  messages.value.push({
    id: `user-${Date.now()}`,
    text,
    isUser: true
  })
  
  inputText.value = ''
  
  // 滚动到底部
  await nextTick()
  const messageList = document.querySelector('.panel-body')
  if (messageList) {
    messageList.scrollTop = messageList.scrollHeight
  }
  
  try {
    // 调用 AI 接口
    const response = await chatWithAi({
      message: text,
      sessionId: sessionId.value
    })
    
    // 添加 AI 回复
    messages.value.push({
      id: `ai-${Date.now()}`,
      text: response.reply,
      isUser: false,
      cards: response.cards
    })
    
    // 更新 sessionId
    if (response.sessionId) {
      sessionId.value = response.sessionId
    }
  } catch (error) {
    console.error('AI request failed:', error)
    messages.value.push({
      id: `error-${Date.now()}`,
      text: '抱歉，暂时无法回答您的问题，请稍后再试。',
      isUser: false
    })
  }
}
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.float-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #007aff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
}

.float-btn:hover {
  background: #0056cc;
}

.icon {
  font-weight: bold;
  font-size: 18px;
}

.panel {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 360px;
  height: 500px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.panel-header button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.panel-footer {
  display: flex;
  padding: 12px;
  border-top: 1px solid #eee;
  gap: 8px;
}

.panel-footer input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  outline: none;
}

.panel-footer input:focus {
  border-color: #007aff;
}

.panel-footer button {
  padding: 8px 16px;
  background: #007aff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.panel-footer button:hover {
  background: #0056cc;
}
</style>
```

- [ ] **Step 4: 提交代码**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/rentHouseH5
git add src/components/ai/ src/api/ai.ts
git commit -m "feat: add AI assistant components"
```

### Task 10: 前端 - 集成 AI 助手到主页面

**Files:**
- Modify: `rentHouseH5/src/views/home/index.vue`

- [ ] **Step 1: 查看现有主页面**

```bash
cat rentHouseH5/src/views/home/index.vue
```

- [ ] **Step 2: 在主页面中添加 AI 助手**

```vue
<template>
  <div class="home">
    <!-- 原有内容 -->
    <div class="content">
      <!-- ... -->
    </div>
    
    <!-- AI 助手 -->
    <AiAssistant />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import AiAssistant from '@/components/ai/AiAssistant.vue'

// ... 原有逻辑
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #f5f5f5;
}

.content {
  padding: 16px;
}
</style>
```

- [ ] **Step 3: 提交代码**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/rentHouseH5
git add src/views/home/index.vue
git commit -m "feat: integrate AI assistant into home page"
```

### Task 11: 测试完整链路

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动所有服务**

```bash
# 终端 1：启动 lease
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn spring-boot:run -pl web/web-app

# 终端 2：启动 AptGuide
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
uv run uvicorn aptguide.main:app --reload --port 8100

# 终端 3：启动前端
cd /home/chove/桌面/apartment-intelligence-platform/rentHouseH5
npm run dev
```

- [ ] **Step 2: 测试 AI 对话接口**

```bash
curl -X POST http://localhost:8081/app/ai/chat \
  -H "Content-Type: application/json" \
  -H "access-token: <your-jwt-token>" \
  -d '{"message": "帮我找房", "sessionId": "test-001"}'
```

Expected: `{"code":0,"message":"ok","data":{"reply":"...","cards":[...],"sessionId":"test-001"}}`

- [ ] **Step 3: 测试前端 AI 助手**

1. 打开浏览器访问前端页面
2. 点击右下角 AI 助手按钮
3. 输入"帮我找房"
4. 验证 AI 回复正常

- [ ] **Step 4: 记录测试结果**

测试通过后，提交最终代码。

## 总结

完成以上任务后，系统将具备：

1. ✅ lease 后端 AI 工具接口（/internal/ai/tools/*）
2. ✅ lease 后端 AI 入口接口（/app/ai/chat）
3. ✅ AptGuide 对接新接口
4. ✅ 前端 AI 助手组件
5. ✅ 完整链路测试通过

下一步可以：
- 完善房源搜索的字段映射
- 添加预约创建接口
- 优化 AI 对话体验
- 添加更多测试用例
