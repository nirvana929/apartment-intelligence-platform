"""Lease workflow procedure for AptGuide 2.0 harness."""

from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.tools.contracts import ToolCallRequest


class LeaseWorkflowProcedure:
    """Handles current user's lease queries through governed tools."""

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        if not frame.user_id:
            return ProcedureResult(
                task="lease",
                phase="lease_auth_required",
                reply="请先登录后再查看您的租约。",
                fallback_reason="missing_user_id",
            )
        if tool_runtime is None:
            return ProcedureResult(
                task="lease",
                phase="lease_tool_unavailable",
                reply="租约服务暂时不可用，请稍后再试。",
                fallback_reason="tool_runtime_missing",
            )
        request = ToolCallRequest(
            tool="lease.list_mine",
            request_id=frame.request_id,
            user_id=frame.user_id,
            payload={"user_id": frame.user_id, "limit": 10},
        )
        result = tool_runtime.execute(request)
        if not result.ok:
            return ProcedureResult(
                task="lease",
                phase="lease_list_failed",
                reply="查询租约失败，请稍后再试。",
                fallback_reason="lease_list_failed",
            )
        leases = result.data.get("leases", [])
        cards = [
            {
                "type": "lease_record",
                "lease_id": lease.get("lease_id", ""),
                "room_id": lease.get("room_id", ""),
                "status": lease.get("status", ""),
                "start_date": lease.get("start_date", ""),
                "end_date": lease.get("end_date", ""),
            }
            for lease in leases[:5]
        ]
        return ProcedureResult(
            task="lease",
            phase="lease_list" if cards else "lease_list_empty",
            reply=f"您有{len(leases)}条租约记录。" if cards else "您当前没有租约记录。",
            cards=cards,
            metadata={"lease_count": len(leases)},
        )
