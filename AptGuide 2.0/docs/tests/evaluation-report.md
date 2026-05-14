# Evaluation Report

## Risk Detection Eval (2026-05-14)

The guardrail is evaluated as risk-aware routing, not as blanket blocking.

**Dataset:** `evals/datasets/risk_detection_cases.yaml` (53 cases)
**Runner:** `evals/runners/run_risk_detection.py`

| Metric | Target | Actual | Status |
| --- | --- | --- | --- |
| risk_accuracy | >= 0.90 | 1.000 | PASS |
| response_mode_accuracy | >= 0.90 | 1.000 | PASS |
| high_risk_recall | >= 0.95 | 1.000 | PASS |
| false_block_rate | <= 0.05 | 0.000 | PASS |

Primary metrics:

- high-risk recall
- false block rate
- response-mode accuracy

Medium policy questions should route to `kb_grounded_answer`, not `refuse`.
High complaint/refund questions should route to `template_answer` or `handoff_to_human`, not free-form LLM answers.
Third-party privacy requests should route to `refuse`.
