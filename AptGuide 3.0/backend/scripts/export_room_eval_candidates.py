"""Export room eval candidates from live RAG for human review.

Reads room_search cases from the eval dataset, runs each through ChatService,
and writes returned room cards to a reviewable markdown report.

Usage:
  uv run python scripts/export_room_eval_candidates.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from aptguide3.api.deps import get_chat_service
from aptguide3.domain.conversation import ConversationFrame

DATASET_PATH = Path(__file__).resolve().parent.parent / "evals" / "datasets" / "rag_retrieval_cases.yaml"
REPORT_PATH = Path(__file__).resolve().parent.parent / "evals" / "reports" / "room-eval-candidates.md"


def export_candidates() -> None:
    with open(DATASET_PATH, encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    room_cases = [c for c in cases if c.get("task") == "room_search"]
    service = get_chat_service()

    lines = [
        "# Room Eval Candidates",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Source: `{DATASET_PATH}`",
        "",
    ]

    for case in room_cases:
        case_id = case["id"]
        query = case["query"]
        lines.append(f"## {case_id}")
        lines.append(f"**Query:** {query}")
        lines.append("")

        try:
            frame = ConversationFrame(
                message=query,
                session_id=f"eval-{case_id}",
                user_id="eval-export",
            )
            response = service.run(frame)
            cards = response.cards if hasattr(response, "cards") else []
            if not cards:
                lines.append("No room cards returned.")
                lines.append("")
                continue

            lines.append("| room_id | title | district | rent | wechat_room_id | lease_room_id | evidence_level |")
            lines.append("|---------|-------|----------|------|----------------|---------------|----------------|")
            for card in cards:
                rid = card.get("room_id", "") if isinstance(card, dict) else getattr(card, "room_id", "")
                title = card.get("title", "") if isinstance(card, dict) else getattr(card, "title", "")
                district = card.get("district_name", "") if isinstance(card, dict) else getattr(card, "district_name", "")
                rent = card.get("rent", "") if isinstance(card, dict) else getattr(card, "rent", "")
                wechat_id = card.get("wechat_room_id", "") if isinstance(card, dict) else getattr(card, "wechat_room_id", "")
                lease_id = card.get("lease_room_id", "") if isinstance(card, dict) else getattr(card, "lease_room_id", "")
                evidence = card.get("evidence_level", "") if isinstance(card, dict) else getattr(card, "evidence_level", "")
                lines.append(f"| {rid} | {title} | {district} | {rent} | {wechat_id} | {lease_id} | {evidence} |")
            lines.append("")
        except Exception as e:
            lines.append(f"Error: {e}")
            lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    export_candidates()
