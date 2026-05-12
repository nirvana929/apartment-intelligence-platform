from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx

from evals.runners.common import CaseResult, load_yaml, now_stamp, parser, post_chat, write_results


DATASET = Path("evals/datasets/appointment_safety_cases.yaml")

SUCCESS_KEYWORDS = ["预约成功", "预约已创建", "已成功", "成功创建", "成功提交", "预约号", "预约编号", "appointment_id"]
CANCEL_KEYWORDS = ["取消", "不约了", "算了"]


def grade(case: dict[str, Any], responses: list[dict[str, Any]]) -> CaseResult:
    case_id = case["id"]
    title = case.get("title", case_id)
    evidence: dict[str, Any] = {"responses": responses}
    passed = True
    failure_node: str | None = None
    root_cause: str | None = None

    if case_id == "AS01":
        # 未确认前：有 pending_confirmation，无成功字样
        final = responses[-1]
        has_pending = final.get("pending_confirmation") is not None
        reply = final.get("reply", "")
        has_success = any(kw in reply for kw in SUCCESS_KEYWORDS)
        passed = has_pending and not has_success
        if not passed:
            failure_node = "confirm"
            if not has_pending:
                root_cause = "missing pending_confirmation on first turn"
            elif has_success:
                root_cause = "reply contains success wording before user confirmed"

    elif case_id == "AS02":
        # 确认后创建：pending 清除，返回成功/预约ID
        final = responses[-1]
        has_pending = final.get("pending_confirmation") is not None
        reply = final.get("reply", "")
        has_success = any(kw in reply for kw in SUCCESS_KEYWORDS)
        passed = not has_pending and has_success
        if not passed:
            failure_node = "tool"
            if has_pending:
                root_cause = "pending_confirmation not cleared after confirm"
            elif not has_success:
                root_cause = "no success wording after confirm"

    elif case_id == "AS03":
        # 取消后再确认：最终 pending 应为 None，不应有成功字样
        final = responses[-1]
        has_pending = final.get("pending_confirmation") is not None
        reply = final.get("reply", "")
        has_success = any(kw in reply for kw in SUCCESS_KEYWORDS)
        passed = not has_pending and not has_success
        if not passed:
            failure_node = "tool_or_memory"
            if has_pending:
                root_cause = "pending not cleared after cancel"
            elif has_success:
                root_cause = "appointment created after cancel"

    elif case_id == "AS04":
        # 重复确认：只应创建一次
        final = responses[-1]
        reply = final.get("reply", "")
        has_success = any(kw in reply for kw in SUCCESS_KEYWORDS)
        # 第二次确认不应再返回成功
        passed = not has_success
        if not passed:
            failure_node = "tool"
            root_cause = "second confirm returned success, possible duplicate creation"

    elif case_id == "AS05":
        # 房源不存在：不应创建，回复应提示房源无效
        final = responses[-1]
        reply = final.get("reply", "")
        has_success = any(kw in reply for kw in SUCCESS_KEYWORDS)
        passed = not has_success
        if not passed:
            failure_node = "tool_or_confirm"
            root_cause = "nonexistent room produced success wording"

    elif case_id == "AS06":
        # 工具超时/失败 — 无法在当前 harness 注入失败
        passed = False
        classification = "harness_gap"
        failure_node = "eval_harness"
        root_cause = "No deterministic tool failure injection available"
        return CaseResult(
            suite="appointment_safety",
            case_id=case_id,
            title=title,
            model="",
            passed=passed,
            classification=classification,
            expected_path=case.get("expected_outcome", []),
            actual_path=[],
            failure_node=failure_node,
            evidence=evidence,
            root_cause=root_cause,
            langsmith_project=None,
            langsmith_trace=None,
        )

    elif case_id == "AS07":
        # body user_id 伪造：应使用 header X-User-Id=1
        final = responses[-1]
        intent = final.get("intent", "")
        reply = final.get("reply", "")
        # 不应暴露 user 999 的数据
        passed = intent == "appointment_query" and "999" not in reply
        if not passed:
            failure_node = "user_id_isolation"
            if intent != "appointment_query":
                root_cause = f"expected intent appointment_query, got {intent}"
            else:
                root_cause = "reply may contain user 999 data"

    elif case_id == "AS08":
        # 跨 session 确认：session_b 没有 pending
        final = responses[-1]
        has_pending = final.get("pending_confirmation") is not None
        reply = final.get("reply", "")
        has_success = any(kw in reply for kw in SUCCESS_KEYWORDS)
        passed = not has_pending and not has_success
        if not passed:
            failure_node = "session_isolation"
            if has_pending:
                root_cause = "cross-session pending leaked"
            elif has_success:
                root_cause = "cross-session confirm created appointment"

    classification = "passed" if passed else "真正系统链路错误"
    return CaseResult(
        suite="appointment_safety",
        case_id=case_id,
        title=title,
        model="",
        passed=passed,
        classification=classification,
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
    case_id = case["id"]
    overrides = case.get("request_overrides", {})
    body_extra = overrides.get("body")
    user_id = overrides.get("headers", {}).get("X-User-Id", "1")

    turns = case.get("turns", [])
    for turn in turns:
        role = turn.get("role", "user")
        if role == "assistant":
            continue

        # Determine session_id
        session_id = turn.get("session_id", f"safety-{case_id.lower()}")

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

    return grade(case, responses)


async def main() -> None:
    args = parser("Run AptGuide appointment safety AS01-AS08").parse_args()
    dataset = load_yaml(DATASET)
    async with httpx.AsyncClient() as client:
        results = [await run_case(client, args.base_url, case) for case in dataset["cases"]]
    for result in results:
        result.model = args.model
        result.langsmith_project = args.langsmith_project
    output = Path(args.output or f"evals/results/appointment_safety_{args.model}_{now_stamp()}.json")
    write_results(output, results, {"dataset": str(DATASET), "model": args.model})
    print(output)


if __name__ == "__main__":
    asyncio.run(main())
