from __future__ import annotations

from typing import Any

from aptguide2.harness.composer import ResponseComposer
from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
from aptguide2.harness.memory import MemoryManager
from aptguide2.harness.procedures import ProcedureRuntime
from aptguide2.harness.routing import HybridRouter
from aptguide2.harness.trace import TraceRecorder
from aptguide2.observability.events import emit_event


class AptGuideHarness:
    """系统级编排器 —— AptGuide 2.0 的唯一产品运行时入口。

    串联完整请求生命周期：上下文加载 → 安全检查 → 路由 → 流程执行 →
    记忆更新 → 自动转人工检测 → 响应组装 → trace 记录。

    外部通过 run() 或 run_async() 传入 AptGuideRequest，得到 AptGuideResponse。
    """

    def __init__(
        self,
        context_store: Any,                # ContextStore 实现（InMemory 或 Persistent）
        router: HybridRouter,              # 路由器
        procedure_runtime: ProcedureRuntime,  # 流程执行器
        include_trace: bool = False,       # 是否在响应中附带 trace（生产环境通常关闭）
        tool_runtime: Any | None = None,   # ToolRuntime，传递给 procedure 使用
    ) -> None:
        self.context_store = context_store
        self.router = router
        self.procedure_runtime = procedure_runtime
        self.composer = ResponseComposer(include_trace=include_trace)
        self.tool_runtime = tool_runtime
        self.memory = MemoryManager()

    def run(self, request: AptGuideRequest) -> AptGuideResponse:
        """Synchronous run — for tests and backward compatibility."""
        import asyncio

        return asyncio.run(self.run_async(request))

    async def run_async(self, request: AptGuideRequest) -> AptGuideResponse:
        """异步主流程 —— harness 的核心编排逻辑。"""

        recorder = TraceRecorder(request_id=request.request_id, session_id=request.session_id)

        # ── 阶段 1：加载会话上下文 ──
        # 从 ContextStore 恢复上次会话状态（phase、pending_action、recent_messages 等）
        token = recorder.start_stage(
            "context.load",
            "in_memory_v1",
            {"session_id": request.session_id, "message_len": len(request.message)},
        )
        if hasattr(self.context_store, 'load_async'):
            frame = await self.context_store.load_async(request)
        else:
            frame = self.context_store.load(request)
        # 检查 pending_action 是否已过期（TTL 300s），过期则清除
        self.memory.check_pending_action_expiry(frame)
        recorder.finish_stage(token, {"phase": frame.phase, "has_pending_action": frame.pending_action is not None})

        # ── 阶段 2：路由决策 ──
        # HybridRouter 按优先级判断：safety > pending_action > semantic intent
        token = recorder.start_stage("routing", self.router.name, {"message": request.message[:80]})
        decision = self.router.route(frame)
        recorder.finish_stage(
            token,
            {
                "task": decision.task,
                "procedure": decision.procedure,
                "domain_category": decision.domain_category,
            },
        )

        # ── 阶段 3：执行 procedure ──
        # ProcedureRuntime 根据 decision.procedure 分发到具体模块
        token = recorder.start_stage("procedure.run", decision.procedure, {"task": decision.task})
        result = self.procedure_runtime.run(frame, decision, tool_runtime=self.tool_runtime)
        recorder.finish_stage(
            token,
            {
                "phase": result.phase,
                "card_count": len(result.cards),
                "source_count": len(result.sources),
                "fallback_reason": result.fallback_reason,
            },
        )

        # ── 阶段 3.5：自动转人工检测 ──
        # 如果连续 2 次工具调用失败，且当前不是 handoff，自动切换到 handoff.tool_failure
        if (
            result.task != "handoff"
            and self.memory.get_consecutive_tool_failures(frame) >= 2
            and self.procedure_runtime.has("handoff.tool_failure")
        ):
            handoff_decision = decision.model_copy(
                update={
                    "task": "handoff",
                    "procedure": "handoff.tool_failure",
                    "confidence": 0.9,
                    "domain_category": "handoff",
                    "reason": "consecutive tool failures",
                }
            )
            token = recorder.start_stage("procedure.run", "handoff.tool_failure", {"task": "handoff"})
            result = self.procedure_runtime.run(frame, handoff_decision, tool_runtime=self.tool_runtime)
            recorder.finish_stage(
                token,
                {
                    "phase": result.phase,
                    "card_count": len(result.cards),
                    "source_count": len(result.sources),
                    "fallback_reason": result.fallback_reason,
                },
            )
            decision = handoff_decision

        # ── 阶段 4：更新会话状态 ──
        # 将 procedure 结果写回 frame，供下一轮上下文使用
        frame.phase = result.phase
        frame.active_task = result.task
        if result.cards:
            frame.last_recommendations = result.cards
        if result.pending_action:
            frame.pending_action = result.pending_action
        # 追加本轮 user message + assistant reply 到 recent_messages（上限 12 条）
        self.memory.update_recent_messages(frame, assistant_reply=result.reply)
        # 持久化会话帧
        if hasattr(self.context_store, 'save_async'):
            await self.context_store.save_async(frame)
        else:
            self.context_store.save(frame)

        # ── 阶段 5：组装响应 + 发射事件 ──
        trace = recorder.to_trace()
        emit_event(
            "harness.completed",
            request_id=request.request_id,
            trace_id=trace.trace_id,
            session_id=request.session_id,
            task=result.task,
            phase=result.phase,
            stage_count=len(trace.stages),
            card_count=len(result.cards),
            source_count=len(result.sources),
        )
        return self.composer.compose(frame, decision, result, trace)
