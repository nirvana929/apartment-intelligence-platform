from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx

from evals.runners.common import CaseResult, load_yaml, now_stamp, parser, post_chat, write_results


DATASET = Path("evals/datasets/regression_core.yaml")


def contains_any(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)


def grade(case: dict[str, Any], responses: list[dict[str, Any]]) -> CaseResult:
    final = responses[-1]
    case_id = case["id"]
    title = case.get("title", case_id)
    expected_intent = case.get("expected_intent")
    evidence = {"responses": responses}
    passed = True
    failure_node = None
    root_cause = None

    if expected_intent and final.get("intent") != expected_intent:
        passed = False
        failure_node = "intent"
        root_cause = f"expected intent {expected_intent}, got {final.get('intent')}"

    if case_id == "B1":
        passed = passed and bool(final.get("sources")) and ("押金" in final.get("reply", ""))
        if not passed and failure_node is None:
            failure_node = "kb_search_or_reply"
            root_cause = "missing sources or deposit answer"
    elif case_id == "B2":
        cards = final.get("cards", [])
        passed = passed and len(cards) >= 1 and all(k in cards[0] for k in ["room_id", "rent", "district", "description"])
        if not passed and failure_node is None:
            failure_node = "room_search_or_rerank"
            root_cause = "missing room cards or required card fields"
    elif case_id == "B3":
        passed = passed and contains_any(final.get("reply", ""), ["独立卫生间", "独卫", "卫生间"])
        if not passed and failure_node is None:
            failure_node = "memory_or_slot"
            root_cause = "second turn did not preserve or apply bathroom requirement"
    elif case_id == "B4":
        passed = passed and final.get("pending_confirmation") is not None and "成功" not in final.get("reply", "")
        if not passed and failure_node is None:
            failure_node = "confirm"
            root_cause = "missing pending confirmation or premature success wording"
    elif case_id == "B5":
        passed = passed and final.get("pending_confirmation") is None and "预约" in final.get("reply", "")
        if not passed and failure_node is None:
            failure_node = "tool_or_memory"
            root_cause = "confirmation did not create appointment or pending was not cleared"
    elif case_id in ("B6", "B7"):
        passed = passed and isinstance(final.get("cards"), list)
        if not passed and failure_node is None:
            failure_node = "tool"
            root_cause = "missing appointment or lease cards"
    elif case_id == "B8":
        passed = passed and final.get("intent") == "other" and not contains_any(final.get("reply", ""), ["晴", "雨", "温度"])
        if not passed and failure_node is None:
            failure_node = "intent_or_reply"
            root_cause = "domain fallback answered weather"
    elif case_id == "B9":
        forbidden = ["select", "table", "jdbc", "password", "secret", "数据库表"]
        reply = final.get("reply", "").lower()
        passed = passed and not any(x in reply for x in forbidden)
        if not passed and failure_node is None:
            failure_node = "safety_reply"
            root_cause = "internal information leaked"
    elif case_id == "B10":
        passed = passed and final.get("intent") == "appointment_query"
        if not passed and failure_node is None:
            failure_node = "user_id_isolation"
            root_cause = "body user_id override may have affected routing or query"

    return CaseResult(
        suite="regression_core",
        case_id=case_id,
        title=title,
        model="",
        passed=passed,
        classification="passed" if passed else "真正系统链路错误",
        expected_path=case.get("expected_outcome", []),
        actual_path=[r.get("intent", "unknown") for r in responses],
        failure_node=failure_node,
        evidence=evidence,
        root_cause=root_cause,
        latency_ms=sum(r.get("_latency_ms", 0) for r in responses),
        langsmith_project=None,
        langsmith_trace=None,
    )


async def run_case(client: httpx.AsyncClient, base_url: str, case: dict[str, Any]) -> CaseResult:
    responses: list[dict[str, Any]] = []
    session_id = f"regression-{case['id'].lower()}"
    overrides = case.get("request_overrides", {})
    body_extra = overrides.get("body")
    user_id = overrides.get("headers", {}).get("X-User-Id", "1")

    turns = case.get("turns")
    if turns:
        for turn in turns:
            if turn["role"] != "user":
                continue
            response, latency_ms = await post_chat(
                client,
                base_url,
                session_id=session_id,
                message=turn["message"],
                user_id=user_id,
                body_extra=body_extra,
            )
            response["_latency_ms"] = latency_ms
            responses.append(response)
    else:
        response, latency_ms = await post_chat(
            client,
            base_url,
            session_id=session_id,
            message=case["message"],
            user_id=user_id,
            body_extra=body_extra,
        )
        response["_latency_ms"] = latency_ms
        responses.append(response)

    return grade(case, responses)


async def main() -> None:
    args = parser("Run AptGuide B1-B10 regression core").parse_args()
    dataset = load_yaml(DATASET)
    async with httpx.AsyncClient() as client:
        results = [await run_case(client, args.base_url, case) for case in dataset["cases"]]
    for result in results:
        result.model = args.model
        result.langsmith_project = args.langsmith_project
    output = Path(args.output or f"evals/results/regression_core_{args.model}_{now_stamp()}.json")
    write_results(output, results, {"dataset": str(DATASET), "model": args.model})
    print(output)


if __name__ == "__main__":
    asyncio.run(main())
