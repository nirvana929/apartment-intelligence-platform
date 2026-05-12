"""
AptInsight Targeted Eval Runner

Per-node model override evaluation runner for model selection.
Supports independent model/max_tokens/reasoning_effort configuration
for intent, sql, and answer nodes.

Usage:
    uv run python -m evals.runners.targeted_eval \
      --cases C01,C02,C03 \
      --model-intent qwen-turbo-latest \
      --max-tokens-intent 300 \
      --model-sql qwen-plus-latest \
      --max-tokens-sql 1200 \
      --model-answer qwen-turbo-latest \
      --max-tokens-answer 600 \
      --output evals/reports/targeted/qwen_plus_complex_sql.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aptinsight.agent.graph import (
    _load_metric_context,
    _load_schema_context,
    _route_after_intent,
    _route_after_sql_execution,
    _route_after_sql_generation,
    _route_after_sql_guard,
    _wrap_node,
)
from aptinsight.agent.nodes.build_chart import build_chart
from aptinsight.agent.nodes.execute_sql import execute_sql
from aptinsight.agent.nodes.generate_sql import generate_sql
from aptinsight.agent.nodes.guard_sql import guard_sql
from aptinsight.agent.nodes.intent import classify_intent
from aptinsight.agent.nodes.write_answer import write_answer
from aptinsight.agent.state import (
    INTENT_ANALYSIS,
    INTENT_CHITCHAT,
    INTENT_OUT_OF_SCOPE,
    AgentState,
    create_initial_state,
)
from aptinsight.core.config import settings
from aptinsight.core.logging import get_logger
from aptinsight.llm.client import LLMClient
from evals.runners.text_to_sql import _validate_result
from langgraph.graph import END, StateGraph

logger = get_logger(__name__)


# ============================================================================
# Data classes
# ============================================================================


@dataclass
class TargetedCase:
    id: str
    category: str
    question: str
    expected: dict[str, Any] = field(default_factory=dict)


@dataclass
class TargetedResult:
    # Case identification
    case_id: str
    question: str

    # Model configuration used
    model_intent: str = ""
    model_sql: str = ""
    model_answer: str = ""
    max_tokens_intent: int = 0
    max_tokens_sql: int = 0
    max_tokens_answer: int = 0
    reasoning_effort: str = ""

    # Pipeline results
    actual_intent: str = ""
    intent_reason: str = ""  # Future: capture from raw LLM response
    generated_sql: str = ""
    guard_passed: bool = False
    execution_success: bool = False
    chart_type: str = ""
    answer: str = ""
    error: str | None = None

    # Rich trace
    latency_ms: float = 0.0
    content_length: int = 0
    reasoning_length: int = 0
    json_parse_success: bool = True

    # Failure classification
    is_system_failure: bool = False
    root_cause_category: str = ""

    # Repeat tracking
    repeat_index: int = 0

    # Validation
    passed: bool = False


@dataclass
class TargetedReport:
    config: dict[str, Any] = field(default_factory=dict)
    total_cases: int = 0
    total_runs: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    error_cases: int = 0
    system_failure_cases: int = 0
    pass_rate: float = 0.0
    avg_latency_ms: float = 0.0
    results: list[TargetedResult] = field(default_factory=list)
    root_cause_distribution: dict[str, int] = field(default_factory=dict)


# ============================================================================
# Instrumented LLM Client
# ============================================================================


class InstrumentedLLMClient:
    """
    Wrapper around LLMClient that captures raw response metadata.

    Calls the underlying AsyncOpenAI client directly to access the full
    response object, recording content_length, reasoning_length, and
    JSON parse failures for each LLM call.
    """

    def __init__(self, wrapped: LLMClient):
        self._wrapped = wrapped
        self.model = wrapped.model
        self.default_max_tokens = wrapped.default_max_tokens
        self.reasoning_effort = wrapped.reasoning_effort
        # Trace accumulators (reset per case run)
        self.total_content_length: int = 0
        self.total_reasoning_length: int = 0
        self.json_parse_failures: int = 0

    def reset_trace(self):
        self.total_content_length = 0
        self.total_reasoning_length = 0
        self.json_parse_failures = 0

    def _build_extra(self) -> dict[str, Any] | None:
        if self._wrapped.reasoning_effort:
            return {"reasoning_effort": self._wrapped.reasoning_effort}
        return None

    def _record_trace(self, content: str, response: Any) -> None:
        reasoning_content = ""
        try:
            reasoning_content = (
                response.choices[0].message.model_extra.get("reasoning_content", "")
                or ""
            )
        except Exception:
            pass
        self.total_content_length += len(content)
        self.total_reasoning_length += len(reasoning_content)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> str:
        extra = self._build_extra()
        response = await self._wrapped.client.chat.completions.create(
            model=self._wrapped.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens if max_tokens is not None else self._wrapped.default_max_tokens,
            extra_body=extra,
        )
        content = response.choices[0].message.content or ""
        self._record_trace(content, response)
        return content

    async def chat_structured(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
    ) -> str:
        extra = self._build_extra()
        response = await self._wrapped.client.chat.completions.create(
            model=self._wrapped.model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=max_tokens if max_tokens is not None else self._wrapped.default_max_tokens,
            extra_body=extra,
        )
        content = response.choices[0].message.content or "{}"
        self._record_trace(content, response)

        # Check JSON validity
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json.loads(content[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            self.json_parse_failures += 1

        return content


# ============================================================================
# Targeted graph construction
# ============================================================================


def create_targeted_graph(
    intent_client: Any,
    sql_client: Any,
    answer_client: Any,
):
    """
    Build a LangGraph workflow with explicit per-node LLM clients.

    Mirrors create_agent_graph() from graph.py but accepts pre-configured
    clients instead of reading from global settings.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("classify_intent", _wrap_node(classify_intent, intent_client))
    workflow.add_node("generate_sql", _wrap_node(generate_sql, sql_client))
    workflow.add_node("guard_sql", guard_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("build_chart", build_chart)
    workflow.add_node("write_answer", _wrap_node(write_answer, answer_client))

    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        _route_after_intent,
        {
            INTENT_ANALYSIS: "generate_sql",
            INTENT_CHITCHAT: "write_answer",
            INTENT_OUT_OF_SCOPE: "write_answer",
            "error": "write_answer",
        },
    )
    workflow.add_conditional_edges(
        "generate_sql",
        _route_after_sql_generation,
        {
            "success": "guard_sql",
            "error": "write_answer",
        },
    )
    workflow.add_conditional_edges(
        "guard_sql",
        _route_after_sql_guard,
        {
            "passed": "execute_sql",
            "failed": "write_answer",
        },
    )
    workflow.add_conditional_edges(
        "execute_sql",
        _route_after_sql_execution,
        {
            "success": "build_chart",
            "error": "write_answer",
        },
    )
    workflow.add_edge("build_chart", "write_answer")
    workflow.add_edge("write_answer", END)

    return workflow.compile()


# ============================================================================
# Executor
# ============================================================================


class _TargetedExecutor:
    """Thin wrapper that mirrors AgentExecutor.run() with a pre-built graph."""

    def __init__(self, graph):
        self.graph = graph

    async def run(self, question: str) -> AgentState:
        initial_state = create_initial_state(question=question)
        initial_state["schema_context"] = _load_schema_context()
        initial_state["metric_context"] = _load_metric_context()
        try:
            return await self.graph.ainvoke(initial_state)
        except Exception as e:
            return {
                **initial_state,
                "error": f"Workflow exception: {e}",
                "answer": "Error during execution.",
            }


# ============================================================================
# Failure classification
# ============================================================================


def classify_system_failure(
    result: TargetedResult,
) -> tuple[bool, str]:
    """Classify whether a failure is a system failure and assign root cause."""
    error = result.error or ""
    intent = result.actual_intent

    # Passed: not a failure
    if not error and result.passed:
        return False, ""

    # Legitimate rejections (NOT system failures)
    if intent == "out_of_scope" and not error:
        return False, "legitimate_refusal"
    if intent == "chitchat" and not error:
        return False, "legitimate_chitchat"
    if error and "SQL 安全检查失败" in error:
        return False, "guard_rejected"

    # System failures
    if result.content_length == 0:
        return True, "empty_content"
    if not result.json_parse_success:
        return True, "json_parse_failure"
    if intent == "out_of_scope" and error and "意图识别" in error:
        return True, "intent_classification_failure"
    if error and ("SQL 生成失败" in error or "生成的 SQL 无效" in error):
        return True, "sql_generation_failure"
    if intent == "analysis" and not result.generated_sql and not error:
        return True, "empty_sql_output"
    if error and "SQL 执行失败" in error:
        return True, "database_execution_error"
    if result.content_length < 20 and intent == "analysis":
        return True, "content_truncation"
    if not result.passed and not error:
        return True, "validation_mismatch"
    if error:
        return True, "unknown_error"

    return False, "validation_failed"


# ============================================================================
# Case loading
# ============================================================================


def load_cases(file_path: str) -> list[TargetedCase]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        raise ValueError("Test case file must be a YAML list")
    return [
        TargetedCase(
            id=item.get("id", ""),
            category=item.get("category", ""),
            question=item.get("question", ""),
            expected=item.get("expected", {}),
        )
        for item in data
    ]


# ============================================================================
# Single test execution
# ============================================================================


async def run_single_targeted_test(
    case: TargetedCase,
    args: argparse.Namespace,
    repeat_index: int,
) -> TargetedResult:
    """Run a single test case with fresh clients and graph (concurrency-safe)."""
    result = TargetedResult(
        case_id=case.id,
        question=case.question,
        model_intent=args.model_intent,
        model_sql=args.model_sql,
        model_answer=args.model_answer,
        max_tokens_intent=args.max_tokens_intent,
        max_tokens_sql=args.max_tokens_sql,
        max_tokens_answer=args.max_tokens_answer,
        reasoning_effort=args.reasoning_effort or settings.llm_reasoning_effort,
        repeat_index=repeat_index,
    )

    # Build fresh clients per case for concurrency safety
    api_key = args.api_key or settings.llm_api_key
    base_url = args.base_url or settings.llm_base_url
    reasoning = args.reasoning_effort or settings.llm_reasoning_effort

    intent_client = LLMClient(
        api_key=api_key,
        base_url=base_url,
        model=args.model_intent,
        default_max_tokens=args.max_tokens_intent,
        reasoning_effort=reasoning,
    )
    sql_client = LLMClient(
        api_key=api_key,
        base_url=base_url,
        model=args.model_sql,
        default_max_tokens=args.max_tokens_sql,
        reasoning_effort=reasoning,
    )
    answer_client = LLMClient(
        api_key=api_key,
        base_url=base_url,
        model=args.model_answer,
        default_max_tokens=args.max_tokens_answer,
        reasoning_effort=reasoning,
    )

    intent_instr = InstrumentedLLMClient(intent_client)
    sql_instr = InstrumentedLLMClient(sql_client)
    answer_instr = InstrumentedLLMClient(answer_client)

    graph = create_targeted_graph(intent_instr, sql_instr, answer_instr)
    executor = _TargetedExecutor(graph)

    start = time.monotonic()

    try:
        state = await executor.run(case.question)
        result.latency_ms = (time.monotonic() - start) * 1000

        # Extract pipeline results
        result.actual_intent = state.get("intent", "")
        result.generated_sql = state.get("safe_sql") or state.get("generated_sql") or ""
        guard_result = state.get("sql_guard_result", {})
        result.guard_passed = guard_result.get("passed", False) if isinstance(guard_result, dict) else False
        result.execution_success = bool(state.get("rows"))
        result.chart_type = state.get("chart_type") or ""
        raw_answer = state.get("answer", "")
        # Handle coroutine leak from write_answer node (pre-existing bug)
        if asyncio.iscoroutine(raw_answer):
            raw_answer = f"<coroutine: _generate_failure_answer>"
        result.answer = raw_answer
        result.error = state.get("error")

        # Aggregate trace
        result.content_length = (
            intent_instr.total_content_length
            + sql_instr.total_content_length
            + answer_instr.total_content_length
        )
        result.reasoning_length = (
            intent_instr.total_reasoning_length
            + sql_instr.total_reasoning_length
            + answer_instr.total_reasoning_length
        )
        result.json_parse_success = (
            intent_instr.json_parse_failures == 0
            and sql_instr.json_parse_failures == 0
        )

        # Validate
        agent_result = {
            "answer": result.answer,
            "sql": result.generated_sql,
            "error": result.error,
            "rows": state.get("rows", []),
            "intent": result.actual_intent,
            "chart_type": result.chart_type,
            "sql_guard_result": guard_result,
        }
        result.passed = _validate_result(case.expected, agent_result)

        # Classify failure
        result.is_system_failure, result.root_cause_category = classify_system_failure(
            result
        )

    except Exception as e:
        result.latency_ms = (time.monotonic() - start) * 1000
        result.error = str(e)
        result.is_system_failure = True
        result.root_cause_category = "runner_exception"

    return result


# ============================================================================
# Report generation
# ============================================================================


def generate_report(results: list[TargetedResult], args: argparse.Namespace) -> TargetedReport:
    report = TargetedReport()
    report.config = {
        "model_intent": args.model_intent,
        "model_sql": args.model_sql,
        "model_answer": args.model_answer,
        "max_tokens_intent": args.max_tokens_intent,
        "max_tokens_sql": args.max_tokens_sql,
        "max_tokens_answer": args.max_tokens_answer,
        "reasoning_effort": args.reasoning_effort or settings.llm_reasoning_effort,
        "base_url": args.base_url or settings.llm_base_url,
        "repeat": args.repeat,
    }

    report.results = results
    report.total_runs = len(results)

    unique_cases = {r.case_id for r in results}
    report.total_cases = len(unique_cases)

    passed_cases: set[str] = set()
    failed_cases: set[str] = set()
    error_cases: set[str] = set()
    system_failures: set[str] = set()
    root_causes: dict[str, int] = {}
    total_latency = 0.0

    for r in results:
        total_latency += r.latency_ms
        if r.root_cause_category:
            root_causes[r.root_cause_category] = root_causes.get(r.root_cause_category, 0) + 1
        if r.is_system_failure:
            system_failures.add(r.case_id)
        if r.error:
            error_cases.add(r.case_id)
        elif r.passed:
            passed_cases.add(r.case_id)
        else:
            failed_cases.add(r.case_id)

    report.passed_cases = len(passed_cases)
    report.failed_cases = len(failed_cases)
    report.error_cases = len(error_cases)
    report.system_failure_cases = len(system_failures)
    report.pass_rate = len(passed_cases) / report.total_cases if report.total_cases else 0.0
    report.avg_latency_ms = total_latency / report.total_runs if report.total_runs else 0.0
    report.root_cause_distribution = root_causes

    return report


def save_report(report: TargetedReport, output_path: str) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    report_dict = {
        "config": report.config,
        "summary": {
            "total_cases": report.total_cases,
            "total_runs": report.total_runs,
            "passed_cases": report.passed_cases,
            "failed_cases": report.failed_cases,
            "error_cases": report.error_cases,
            "system_failure_cases": report.system_failure_cases,
            "pass_rate": round(report.pass_rate, 4),
            "avg_latency_ms": round(report.avg_latency_ms, 2),
        },
        "root_cause_distribution": report.root_cause_distribution,
        "results": [
            {
                "case_id": r.case_id,
                "question": r.question,
                "model_intent": r.model_intent,
                "model_sql": r.model_sql,
                "model_answer": r.model_answer,
                "max_tokens_intent": r.max_tokens_intent,
                "max_tokens_sql": r.max_tokens_sql,
                "max_tokens_answer": r.max_tokens_answer,
                "reasoning_effort": r.reasoning_effort,
                "actual_intent": r.actual_intent,
                "intent_reason": r.intent_reason,
                "generated_sql": r.generated_sql,
                "guard_passed": r.guard_passed,
                "execution_success": r.execution_success,
                "chart_type": r.chart_type,
                "answer": r.answer,
                "error": r.error,
                "latency_ms": round(r.latency_ms, 2),
                "content_length": r.content_length,
                "reasoning_length": r.reasoning_length,
                "json_parse_success": r.json_parse_success,
                "is_system_failure": r.is_system_failure,
                "root_cause_category": r.root_cause_category,
                "repeat_index": r.repeat_index,
                "passed": r.passed,
            }
            for r in report.results
        ],
    }

    def _default(obj):
        if asyncio.iscoroutine(obj):
            return f"<coroutine: {getattr(obj, '__name__', '?')}>"
        return str(obj)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2, default=_default)


def print_report(report: TargetedReport) -> None:
    print("\n" + "=" * 60)
    print("Targeted Eval Report")
    print("=" * 60)
    print(f"Config: {report.config['model_intent']} / {report.config['model_sql']} / {report.config['model_answer']}")
    print(f"Cases: {report.total_cases}, Runs: {report.total_runs}")
    print(f"Passed: {report.passed_cases}, Failed: {report.failed_cases}, Errors: {report.error_cases}")
    print(f"System failures: {report.system_failure_cases}")
    print(f"Pass rate: {report.pass_rate:.1%}")
    print(f"Avg latency: {report.avg_latency_ms:.0f}ms")
    if report.root_cause_distribution:
        print(f"Root causes: {report.root_cause_distribution}")
    print("=" * 60)

    # Print per-case summary
    for r in report.results:
        status = "PASS" if r.passed else ("ERR" if r.error else "FAIL")
        sf = " [SYS]" if r.is_system_failure else ""
        print(f"  {r.case_id:6s} [{status}]{sf} {r.latency_ms:7.0f}ms  intent={r.actual_intent}  rc={r.root_cause_category}")


# ============================================================================
# CLI
# ============================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AptInsight Targeted Eval Runner -- per-node model override evaluation"
    )

    # Case selection
    parser.add_argument(
        "--cases", type=str, default="",
        help="Comma-separated case IDs (e.g., C01,C02,C03). Empty = all cases.",
    )
    parser.add_argument(
        "--dataset", type=str,
        default="evals/datasets/text_to_sql_cases.yaml",
        help="Path to test cases YAML file.",
    )

    # Shared connection
    parser.add_argument("--base-url", type=str, default="", help="LLM API base URL.")
    parser.add_argument("--api-key", type=str, default="", help="LLM API key.")

    # Per-node model config
    parser.add_argument("--model-intent", type=str, required=True, help="Model for intent node.")
    parser.add_argument("--max-tokens-intent", type=int, default=400, help="Max tokens for intent node.")
    parser.add_argument("--model-sql", type=str, required=True, help="Model for SQL node.")
    parser.add_argument("--max-tokens-sql", type=int, default=1200, help="Max tokens for SQL node.")
    parser.add_argument("--model-answer", type=str, required=True, help="Model for answer node.")
    parser.add_argument("--max-tokens-answer", type=int, default=1000, help="Max tokens for answer node.")

    # Shared LLM config
    parser.add_argument("--reasoning-effort", type=str, default="", help="Reasoning effort (low/medium/high).")

    # Execution
    parser.add_argument("--repeat", type=int, default=1, help="Run each case N times.")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Max concurrent executions.")

    # Output
    parser.add_argument(
        "--output", type=str,
        default="evals/reports/targeted/targeted_eval.json",
        help="Output JSON report path.",
    )

    return parser.parse_args()


# ============================================================================
# Main
# ============================================================================


async def main():
    args = parse_args()

    # Load and filter cases
    cases = load_cases(args.dataset)
    if args.cases:
        selected_ids = {cid.strip() for cid in args.cases.split(",")}
        cases = [c for c in cases if c.id in selected_ids]
    if not cases:
        print("No test cases matched. Exiting.")
        return

    print(f"Running {len(cases)} cases x {args.repeat} repeats = {len(cases) * args.repeat} total runs")
    print(f"Models: intent={args.model_intent}, sql={args.model_sql}, answer={args.model_answer}")

    # Run cases with concurrency control
    all_results: list[TargetedResult] = []
    semaphore = asyncio.Semaphore(args.max_concurrent)

    async def run_with_semaphore(case: TargetedCase, repeat_idx: int):
        async with semaphore:
            return await run_single_targeted_test(case, args, repeat_idx)

    tasks = []
    for repeat_idx in range(args.repeat):
        for case in cases:
            tasks.append(run_with_semaphore(case, repeat_idx))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            all_results.append(
                TargetedResult(
                    case_id="UNKNOWN", question="", error=str(result),
                    is_system_failure=True, root_cause_category="runner_exception",
                )
            )
        else:
            all_results.append(result)

    # Generate and save report
    report = generate_report(all_results, args)
    save_report(report, args.output)
    print_report(report)
    print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
