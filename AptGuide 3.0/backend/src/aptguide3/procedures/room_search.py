from __future__ import annotations

from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.rag.grounded_answer import build_room_result_message
from aptguide3.rag.planning import build_retrieval_plan


class RoomSearchProcedure:
    name = "room_search"

    def __init__(
        self,
        lease_client: Any = None,
        vector_client: Any = None,
        embedding_client: Any = None,
        preference_scorer: Any = None,
        identity_repo: Any = None,
    ):
        self._lease_client = lease_client
        self._vector_client = vector_client
        self._embedding_client = embedding_client
        self._preference_scorer = preference_scorer
        self._identity_repo = identity_repo

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        if not all([self._lease_client, self._vector_client, self._embedding_client]):
            return self._conservative_fallback(understanding)

        from aptguide3.rag.diagnostics import RoomRecDiagnostic
        from aptguide3.rag.room_retrieval import retrieve_ranked_rooms

        plan = build_retrieval_plan(understanding)
        diagnostic = RoomRecDiagnostic(raw_message=understanding.raw_message)
        rooms = retrieve_ranked_rooms(
            plan,
            self._vector_client,
            self._embedding_client,
            self._lease_client,
            self._preference_scorer,
            top_n=5,
            diagnostic=diagnostic,
            identity_repo=self._identity_repo,
        )

        if not rooms:
            return ProcedureResult(
                message="暂未找到符合条件的房源，请调整筛选条件后重试。",
                phase="room_search",
                metadata={
                    "room_count": 0,
                    "task": understanding.task,
                    "rec_diagnostic": diagnostic.to_report_dict(),
                },
            )

        cards = [_room_card(r) for r in rooms]
        risk_level = plan.risk_level
        message = build_room_result_message(cards, risk_level=risk_level)

        return ProcedureResult(
            message=message,
            phase="room_search",
            cards=cards,
            metadata={
                "route": understanding.route,
                "task": understanding.task,
                "room_count": len(rooms),
                "risk_level": risk_level,
                "rec_diagnostic": diagnostic.to_report_dict(),
            },
        )

    def _conservative_fallback(self, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="已理解您的找房需求。房源检索将在接入 lease 和 vector 后返回可验证结果。",
            phase="room_search",
            metadata={
                "route": understanding.route,
                "task": understanding.task,
                "hard_filters": understanding.hard_filters,
                "soft_preferences": understanding.soft_preferences,
            },
        )


def _room_card(room: Any) -> dict[str, Any]:
    if hasattr(room, "model_dump"):
        data = room.model_dump()
    elif isinstance(room, dict):
        data = room
    else:
        data = {}

    lease_validation_status = data.get("lease_validation_status", "not_checked")
    evidence_level = data.get("evidence_level", "vector_only")

    # Card text must NOT claim rentable/bookable/price-valid unless lease-validated
    if lease_validation_status == "passed":
        availability_status = "已验证可租"
    else:
        availability_status = "仅供参考(未验证)"

    return {
        "type": "room_card",
        "room_id": data.get("room_id", 0),
        "apartment_name": data.get("apartment_name", ""),
        "room_number": data.get("room_number", ""),
        "district_name": data.get("district_name", ""),
        "rent": data.get("rent", 0),
        "payment_types": data.get("payment_types", []),
        "tags": data.get("tags", []),
        "facilities": data.get("facilities", []),
        "is_appointable": data.get("is_appointable", False),
        "final_score": data.get("final_score", 0),
        "recommendation_reason": data.get("recommendation_reason", ""),
        # --- evidence fields ---
        "wechat_room_id": data.get("wechat_room_id", ""),
        "lease_room_id": data.get("lease_room_id"),
        "source_collection": data.get("source_collection", ""),
        "source_record_id": data.get("source_record_id", ""),
        "lease_validation_status": lease_validation_status,
        "evidence_level": evidence_level,
        "matched_query": data.get("matched_query", ""),
        "semantic_score": data.get("semantic_score", 0),
        "availability_status": availability_status,
    }
