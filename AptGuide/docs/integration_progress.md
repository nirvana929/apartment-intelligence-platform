# 公寓智能平台集成进度

> 最后更新: 2026-05-03

## 已完成

### lease 后端
- `3ff2f82` Task 1: AI 工具 VO 类（RoomSearchRequest, RoomVo, RoomSearchResponse）
- `aa09623` Task 2: AiToolController（/internal/ai/tools/*）
- `a16ee47` Task 3: 房源搜索实现（pageItem + getDetailById 转换）
- `d36b910` Task 4: 预约和租约接口（appointment/list-mine, lease/list-mine）
- `70920be` Task 5: InternalTokenInterceptor（/internal/** 鉴权）
- `416b638` Task 8: AiController（/app/ai/chat 入口）
- **修复** InternalTokenInterceptor: 从 X-User-Id 设置 LoginUserHolder（内部 API 浏览历史兼容）
- **修复** RoomInfoServiceImpl: getDetailById 浏览历史保存加 null 检查
- **修复** AiToolController: searchRooms 的 X-User-Id 改为可选

### AptGuide
- `94bec46` Task 6: LeaseToolClient 修复（health check 路径，清理不存在端点）
- **修复** config.py: 补充 lease_base_url、lease_internal_token、lease_request_timeout_seconds
- **修复** .env: LEASE_INTERNAL_TOKEN 更新为真实值
- **修复** tools/client.py: SecretStr 转 str、logger 格式、code 200 兼容
- **修复** agent/nodes/tool.py: 适配 lease 返回格式（list vs dict）、字段名映射
- **修复** schemas/request.py + agent/state.py: 新增 user_id 字段传递
- **修复** api/chat.py: user_id 透传到 state

### 前端 rentHouseH5（未 commit）
- Task 9: ChatMessage.vue, AiAssistant.vue, api/ai/index.ts
- Task 10: 集成到 layout/index.vue

## 测试结果（2026-05-03）

全部通过：
- ✅ lease 健康检查
- ✅ 房源搜索（Milvus 召回 + lease 精确校验）
- ✅ 预约查询
- ✅ 租约查询
- ✅ 知识库问答（押金退还等）
- ✅ 完整 Agent 链路（intent → slot → room_search → rerank → reply）

## 待完成

1. **前端 commit** — rentHouseH5 的改动需要提交
2. **预约创建测试** — 需要用户确认流程的端到端测试
3. **错误处理增强** — lease 接口超时/失败时的降级策略

## 架构原则（用户反馈）
- AI 接口必须独立于前端接口，不改现有 service/mapper
- AI controller 可以注入 UserInfoService 等现有 service 来查询，但不能给现有 service 加新方法
- 现有 LeaseAgreementService 已恢复原状（listByUserId 已移除）

## 关键文件
- lease VO: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/`
- lease Controller: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/`
- lease Config: `lease/web/web-app/src/main/resources/application.yml`
- AptGuide Client: `AptGuide/src/aptguide/tools/client.py`
- 前端 AI: `rentHouseH5/src/components/ai/` 和 `rentHouseH5/src/api/ai/`
