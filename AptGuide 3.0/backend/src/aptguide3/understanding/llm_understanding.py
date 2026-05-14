from __future__ import annotations

from pydantic import ValidationError

from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.understanding.prompts import UNDERSTANDING_SYSTEM_PROMPT
from aptguide3.understanding.validation import clarification_result, validate_or_clarify


class LLMUnderstanding:
    def __init__(self, client, model: str, min_confidence: float = 0.65) -> None:
        self.client = client
        self.model = model
        self.min_confidence = min_confidence

    def understand(self, message: str) -> UnderstandingResult:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": UNDERSTANDING_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            result = UnderstandingResult.model_validate_json(content)
        except (ValidationError, Exception) as exc:
            return clarification_result(message, f"llm_understanding_failed:{exc.__class__.__name__}")

        if not result.raw_message:
            result = result.model_copy(update={"raw_message": message})
        return validate_or_clarify(result, self.min_confidence)
