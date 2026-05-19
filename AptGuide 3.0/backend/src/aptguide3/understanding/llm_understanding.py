from __future__ import annotations

from pydantic import ValidationError

from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.understanding.diagnostics import UnderstandingDiagnostic
from aptguide3.understanding.prompts import UNDERSTANDING_SYSTEM_PROMPT
from aptguide3.understanding.validation import clarification_result, validate_or_clarify, validation_failure_reason


class LLMUnderstanding:
    def __init__(self, client, model: str, min_confidence: float = 0.65, diagnostics_enabled: bool = False) -> None:
        self.client = client
        self.model = model
        self.min_confidence = min_confidence
        self.diagnostics_enabled = diagnostics_enabled
        self.last_diagnostic: UnderstandingDiagnostic | None = None

    def understand(self, message: str) -> UnderstandingResult:
        diagnostic = UnderstandingDiagnostic(raw_message=message)
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
            diagnostic.raw_llm_json = content
            result = UnderstandingResult.model_validate_json(content)
            diagnostic.parsed_route = result.route
            diagnostic.parsed_task = result.task
            diagnostic.parsed_domain = result.domain
            diagnostic.parsed_confidence = result.confidence
            diagnostic.parsed_clarification_needed = result.clarification.needed
            diagnostic.parsed_clarification_question = result.clarification.question
            diagnostic.parsed_risk_response_mode = result.risk.response_mode
            diagnostic.parsed_hard_filters = dict(result.hard_filters)
        except (ValidationError, Exception) as exc:
            diagnostic.parse_error = exc.__class__.__name__
            final = clarification_result(message, f"llm_understanding_failed:{exc.__class__.__name__}")
            diagnostic.validator_reason = final.reason
            diagnostic.final_route = final.route
            diagnostic.final_task = final.task
            diagnostic.final_domain = final.domain
            diagnostic.final_confidence = final.confidence
            self.last_diagnostic = diagnostic
            return final

        if not result.raw_message:
            result = result.model_copy(update={"raw_message": message})

        diagnostic.validator_reason = validation_failure_reason(result, self.min_confidence)
        final = validate_or_clarify(result, self.min_confidence)
        diagnostic.final_route = final.route
        diagnostic.final_task = final.task
        diagnostic.final_domain = final.domain
        diagnostic.final_confidence = final.confidence
        self.last_diagnostic = diagnostic
        return final
