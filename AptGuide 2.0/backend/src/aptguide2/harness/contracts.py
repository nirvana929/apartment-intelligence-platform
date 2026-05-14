from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────
# AptGuide 2.0 Harness 核心契约层
# 定义整个 harness 系统的数据模型：请求、会话帧、路由决策、
# 流程结果、trace 和最终响应。所有模块通过这些模型通信。
# ─────────────────────────────────────────────────────────────

# 支持的 9 种任务类型，由路由模块产出
Task = Literal[
    "room_search",      # 找房
    "kb_qa",            # 知识库问答
    "appointment",      # 预约（创建/取消/列表）
    "lease",            # 租约查询
    "user_data",        # 用户数据
    "memory",           # 长期记忆管理
    "handoff",          # 转人工
    "capability",       # 能力介绍（"你是谁"）
    "fallback",         # 安全兜底 / 超出范围
]
RiskLevel = Literal["low", "medium", "high"]


class AptGuideRequest(BaseModel):
    """API 层传入 harness 的请求模型，对应 POST /chat 的请求体。"""

    session_id: str | None = None          # 会话 ID，用于跨轮次上下文恢复
    request_id: str                        # 本次请求唯一 ID
    user_id: str | None = None             # 用户 ID，预约/租约操作需要
    message: str = ""                      # 用户当前轮次的消息文本
    action: dict[str, Any] | None = None   # 前端传入的动作（如 confirm/cancel 的 confirmation_id）
    client_context: dict[str, Any] = Field(default_factory=dict)  # 客户端额外上下文
    harness_version: str = "harness_v1"    # harness 版本标识


class ConversationFrame(BaseModel):
    """会话帧 —— harness 内部的核心上下文对象，在整个请求生命周期中流转。

    由 ContextStore 加载，经过路由、流程执行、记忆更新后保存。
    每个字段都可能被多个模块读写。
    """

    session_id: str | None = None
    request_id: str
    user_id: str | None = None
    message: str = ""                      # 当前轮次用户消息
    action: dict[str, Any] | None = None   # 前端传入的 action（确认/取消等）
    phase: str = "idle"                    # 当前对话阶段（idle/room_results/awaiting_confirmation 等）
    domain_category: str = "unknown"       # 领域分类（in_domain_task/blocked/unknown 等）
    active_task: Task | None = None        # 当前活跃的任务类型
    task_slots: dict[str, Any] = Field(default_factory=dict)        # 任务槽位（如预约的 room_id、时间等）
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)  # 最近 N 轮消息（上限由 MemoryManager 控制）
    rolling_summary: str = ""              # 历史对话的滚动摘要（预留，当前未使用）
    long_term_profile: dict[str, Any] = Field(default_factory=dict) # 用户长期偏好画像
    pending_action: dict[str, Any] | None = None  # 待确认的动作（如预约确认，含 TTL）
    last_recommendations: list[dict[str, Any]] = Field(default_factory=list)  # 上一轮推荐的房源/KB 来源
    tool_observations: list[dict[str, Any]] = Field(default_factory=list)     # 工具执行观察记录（用于失败计数）
    recovery_decision: dict[str, Any] | None = None  # 恢复策略决策（预留）
    handoff: dict[str, Any] | None = None  # 人工接管状态（含摘要、触发原因）


class RouteDecision(BaseModel):
    """路由决策 —— HybridRouter 的输出，决定本次请求交给哪个 procedure 处理。"""

    task: Task                             # 任务类型
    procedure: str                         # 目标 procedure 名称（如 "rag.room_search"、"appointment.workflow"）
    confidence: float = Field(ge=0.0, le=1.0)  # 路由置信度
    risk_level: RiskLevel = "low"          # 风险等级，高风险会触发更严格的处理
    domain_category: str = "unknown"       # 领域分类
    reason: str = ""                       # 路由原因（用于 debug 和 trace）
    safety_flags: list[str] = Field(default_factory=list)  # 安全标记（guarantee/privacy/out_of_domain）
    metadata: dict[str, Any] = Field(default_factory=dict) # 额外元数据（如 intent 分类详情）


class ProcedureResult(BaseModel):
    """流程执行结果 —— 每个 Procedure 的输出，交给 ResponseComposer 组装最终响应。"""

    task: Task                             # 任务类型
    phase: str                             # 执行后的对话阶段
    reply: str = ""                        # 给用户的回复文本
    cards: list[dict[str, Any]] = Field(default_factory=list)       # 结构化卡片（房源卡片、KB 来源等）
    actions: list[dict[str, Any]] = Field(default_factory=list)     # 可用操作列表
    pending_action: dict[str, Any] | None = None  # 待确认动作
    sources: list[dict[str, Any]] = Field(default_factory=list)     # KB 引用来源
    metadata: dict[str, Any] = Field(default_factory=dict)          # 额外元数据
    fallback_reason: str = ""              # 兜底原因（当 task=fallback 时）


class StageTrace(BaseModel):
    """单个执行阶段的 trace 记录，包含耗时和摘要，不含思维链。"""

    stage: str                             # 阶段名称（如 "context.load"、"routing"、"procedure.run"）
    strategy: str                          # 使用的策略名称
    input_summary: dict[str, Any] = Field(default_factory=dict)   # 输入摘要
    output_summary: dict[str, Any] = Field(default_factory=dict)  # 输出摘要
    latency_ms: float = 0.0               # 耗时（毫秒）
    errors: list[str] = Field(default_factory=list)               # 错误列表


class AptGuideTrace(BaseModel):
    """完整请求的 trace，由 TraceRecorder 产出，包含所有阶段记录。"""

    trace_id: str
    request_id: str
    session_id: str | None = None
    stages: list[StageTrace] = Field(default_factory=list)


class AptGuideResponse(BaseModel):
    """最终 API 响应模型 —— ResponseComposer 的输出，对应 POST /chat 的响应体。"""

    session_id: str | None = None
    request_id: str
    trace_id: str
    reply: str                             # 用户可见的回复文本
    phase: str                             # 当前对话阶段
    domain_category: str                   # 领域分类
    cards: list[dict[str, Any]] = Field(default_factory=list)       # 结构化卡片
    actions: list[dict[str, Any]] = Field(default_factory=list)     # 可用操作
    pending_action: dict[str, Any] | None = None  # 待确认动作
    sources: list[dict[str, Any]] = Field(default_factory=list)     # KB 来源
    metadata: dict[str, Any] = Field(default_factory=dict)          # 元数据（含路由置信度、procedure 名等）
    trace: AptGuideTrace | None = None     # 仅当 include_trace=True 时附带
