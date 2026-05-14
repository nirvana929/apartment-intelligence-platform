from __future__ import annotations

from typing import Protocol

from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.interaction.entity_resolution import normalize_entities
from aptguide2.interaction.validation import build_clarification_intent, validate_or_clarify_intent
from aptguide2.rag.risk_detection import detect_risk_profile


class InteractionClassifier(Protocol):
    def classify(self, message: str) -> InteractionIntent:
        ...


class ClarifyingInteractionClassifier:
    def classify(self, message: str) -> InteractionIntent:
        return build_clarification_intent(message, "no_llm_available")


HeuristicInteractionClassifier = ClarifyingInteractionClassifier


class LLMInteractionClassifier:
    def __init__(self, client, model: str, min_confidence: float = 0.65) -> None:
        self.client = client
        self.model = model
        self.min_confidence = min_confidence

    def classify(self, message: str) -> InteractionIntent:
        import json

        from aptguide2.interaction.prompts import INTERACTION_INTENT_SYSTEM_PROMPT

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTERACTION_INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            if "raw_message" not in parsed:
                parsed["raw_message"] = message
            intent = InteractionIntent.model_validate(parsed)
        except Exception as exc:
            return apply_policy_corrections(build_clarification_intent(message, f"llm_intent_failed:{exc.__class__.__name__}"))

        if not intent.raw_message:
            intent = intent.model_copy(update={"raw_message": message})

        validated = validate_or_clarify_intent(normalize_entities(intent), self.min_confidence)
        return apply_policy_corrections(validated)


def apply_policy_corrections(intent: InteractionIntent) -> InteractionIntent:
    risk = detect_risk_profile(intent.raw_message)
    updates: dict = {"risk_level": risk.risk_level}
    if risk.response_mode == "refuse":
        # Refuse always overrides — safety takes priority over clarification.
        updates.update({"route": "fallback", "rag_task": "none", "needs_tool": False, "needs_kb": False, "needs_room_search": False, "response_mode": risk.response_mode})
    elif intent.action != "clarify" and not intent.clarification_needed:
        updates["response_mode"] = risk.response_mode
    if intent.action in {"create", "cancel", "update_preference", "delete_preference"}:
        updates["needs_confirmation"] = True
    return normalize_entities(intent.model_copy(update=updates))
