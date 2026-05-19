from __future__ import annotations

import asyncio
from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


def _run_async(coro: Any) -> Any:
    """Run an async coroutine from sync code, returning the result."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


class LeaseProcedure:
    name = "lease"

    def __init__(self, lease_client: Any = None, audit_repo: Any = None) -> None:
        self.lease_client = lease_client
        self.audit_repo = audit_repo

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        user_id = frame.user_id
        if not user_id:
            return ProcedureResult(
                message="请先登录后查看租约信息。",
                phase="lease",
                metadata={"error": "no_user_id"},
            )

        if not self.lease_client:
            return ProcedureResult(
                message="租约服务暂时不可用，请稍后重试。",
                phase="lease",
                metadata={"error": "no_lease_client"},
            )

        # Query leases
        try:
            leases = _run_async(self.lease_client.list_leases(int(user_id)))
        except Exception:
            leases = []

        # Audit
        if self.audit_repo:
            try:
                _run_async(
                    self.audit_repo.append_audit_event(
                        user_id, frame.session_id, "lease_query",
                        {"lease_count": len(leases)},
                    )
                )
            except Exception:
                pass

        if not leases:
            return ProcedureResult(
                message="暂无租约信息，如需租房请咨询房源搜索。",
                phase="lease",
                metadata={"lease_count": 0},
            )

        # Build result cards
        cards = []
        for lease in leases[:5]:  # limit to 5
            cards.append({
                "type": "lease_card",
                "lease_id": lease.get("lease_id", ""),
                "apartment_name": lease.get("apartment_name", ""),
                "room_number": lease.get("room_number", ""),
                "status": lease.get("status", ""),
                "start_date": lease.get("start_date", ""),
                "end_date": lease.get("end_date", ""),
                "rent": lease.get("rent", 0),
            })

        return ProcedureResult(
            message=f"找到 {len(leases)} 条租约信息。",
            phase="lease",
            cards=cards,
            metadata={"lease_count": len(leases)},
        )
