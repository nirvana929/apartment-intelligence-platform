"""Query understanding that builds results from LLM interaction intent.

When no interaction_intent is provided, returns a clarification fallback.
All keyword extraction has been removed from the runtime path.
"""

from __future__ import annotations

from typing import Any

from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.rag.schemas import QueryUnderstandingResult


def understand_query(
    message: str,
    previous_state: dict[str, Any] | None = None,
    interaction_intent: InteractionIntent | None = None,
) -> QueryUnderstandingResult:
    if interaction_intent is None:
        return QueryUnderstandingResult(
            raw_message=message,
            task="fallback",
            domain="unknown",
            response_mode="ask_clarification",
        )

    if interaction_intent.route != "rag" or interaction_intent.rag_task == "none":
        return QueryUnderstandingResult(
            raw_message=message,
            task="fallback",
            domain=interaction_intent.domain,
            response_mode="ask_clarification",
        )

    return QueryUnderstandingResult(
        raw_message=message,
        task=interaction_intent.rag_task,
        domain=interaction_intent.domain,
        reference_resolution=interaction_intent.reference,
        hard_filters=dict(interaction_intent.hard_filters),
        soft_preferences=list(interaction_intent.soft_preferences),
        retrieval_queries=list(interaction_intent.retrieval_queries),
        risk_level=interaction_intent.risk_level,
        response_mode=interaction_intent.response_mode,
    )
