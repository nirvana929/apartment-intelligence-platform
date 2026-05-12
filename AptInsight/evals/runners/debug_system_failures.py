"""
系统失败根因调查脚本 v2

直接调用 OpenAI API，捕获完整响应对象（包括 reasoning_content 和 usage）。
用于定位 V03/P01/C01/C03 的真正失败原因。

用法：
    cd AptInsight
    uv run python -m evals.runners.debug_system_failures
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from openai import AsyncOpenAI

from aptinsight.agent.nodes.intent import _parse_intent_response, INTENT_PROMPT
from aptinsight.agent.nodes.generate_sql import _parse_sql_response, _validate_sql, SQL_GENERATION_PROMPT
from aptinsight.agent.graph import _load_schema_context, _load_metric_context
from aptinsight.core.config import settings


CASES = [
    {"id": "V03", "question": "最近一个月的评价数量趋势"},
    {"id": "P01", "question": "有多少个已发布的公寓"},
    {"id": "C01", "question": "预约量高但签约量低的公寓有哪些"},
    {"id": "C03", "question": "租金和评分的关系是什么"},
]


async def call_llm_raw(client: AsyncOpenAI, messages: list, max_tokens: int, label: str) -> dict:
    """直接调用 API，返回完整的原始响应信息"""
    extra = {}
    if settings.llm_reasoning_effort:
        extra["reasoning_effort"] = settings.llm_reasoning_effort

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.1,
        max_tokens=max_tokens,
        extra_body=extra if extra else None,
    )

    msg = response.choices[0].message
    content = msg.content or ""

    # 尝试获取 reasoning_content（MiMo 特有字段）
    reasoning_content = ""
    try:
        reasoning_content = msg.model_extra.get("reasoning_content", "") or ""
    except Exception:
        pass

    usage_info = {}
    if response.usage:
        usage_info = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        # 尝试获取 reasoning_tokens（MiMo 特有）
        try:
            usage_info["reasoning_tokens"] = response.usage.model_extra.get("reasoning_tokens", 0)
        except Exception:
            pass

    result = {
        "content": content,
        "content_length": len(content),
        "reasoning_content": reasoning_content,
        "reasoning_content_length": len(reasoning_content),
        "finish_reason": response.choices[0].finish_reason,
        "usage": usage_info,
    }

    print(f"\n  [{label}] content_length={len(content)}, reasoning_length={len(reasoning_content)}, "
          f"finish_reason={response.choices[0].finish_reason}")
    print(f"  [{label}] usage={usage_info}")

    return result


async def investigate_case(case: dict, client: AsyncOpenAI) -> dict:
    """调查单个 case 的完整链路"""
    case_id = case["id"]
    question = case["question"]

    print(f"\n{'='*70}")
    print(f"Case {case_id}: {question}")
    print(f"{'='*70}")

    result = {"case_id": case_id, "question": question}

    # ---- Step 1: Intent Classification ----
    intent_prompt = INTENT_PROMPT.format(question=question)
    intent_raw = await call_llm_raw(
        client,
        messages=[{"role": "user", "content": intent_prompt}],
        max_tokens=settings.llm_max_tokens_intent,
        label="intent",
    )

    result["intent_raw"] = intent_raw

    # 解析 intent
    parsed_intent = _parse_intent_response(intent_raw["content"])
    result["parsed_intent"] = parsed_intent.get("intent")
    result["parsed_reason"] = parsed_intent.get("reason")

    print(f"  -> parsed_intent: {result['parsed_intent']}")
    print(f"  -> parsed_reason: {result['parsed_reason']}")

    if intent_raw["content"]:
        print(f"  -> raw content:\n{intent_raw['content'][:300]}")

    # ---- Step 2: SQL Generation (if intent == analysis) ----
    result["sql_raw"] = None
    result["parsed_sql"] = None

    if result["parsed_intent"] == "analysis":
        schema_context = _load_schema_context()
        metric_context = _load_metric_context()
        sql_prompt = SQL_GENERATION_PROMPT.format(
            question=question,
            schema_context=schema_context,
            metric_context=metric_context,
        )

        sql_raw = await call_llm_raw(
            client,
            messages=[{"role": "user", "content": sql_prompt}],
            max_tokens=settings.llm_max_tokens_sql,
            label="sql",
        )

        result["sql_raw"] = sql_raw

        try:
            parsed_sql = _parse_sql_response(sql_raw["content"])
            result["parsed_sql"] = parsed_sql.get("sql")
            result["tables_used"] = parsed_sql.get("tables_used")

            validation_error = _validate_sql(parsed_sql.get("sql", ""))
            result["validation_error"] = validation_error

            print(f"  -> parsed_sql: {parsed_sql.get('sql', '')[:100]}")
            print(f"  -> validation_error: {validation_error}")
        except Exception as e:
            result["parse_error"] = str(e)
            print(f"  -> SQL parse error: {e}")

        if sql_raw["content"]:
            print(f"  -> raw sql content:\n{sql_raw['content'][:500]}")

    return result


async def main():
    print("=" * 70)
    print("AptInsight System Failure Root Cause Investigation v2")
    print("=" * 70)
    print(f"Model: {settings.llm_model}")
    print(f"Max tokens intent: {settings.llm_max_tokens_intent}")
    print(f"Max tokens SQL: {settings.llm_max_tokens_sql}")
    print(f"Reasoning effort: {settings.llm_reasoning_effort}")

    client = AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=settings.llm_timeout_seconds,
    )

    all_results = []
    for case in CASES:
        result = await investigate_case(case, client)
        all_results.append(result)

    # ---- Summary ----
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for r in all_results:
        cid = r["case_id"]
        intent = r["parsed_intent"]
        content_len = r["intent_raw"]["content_length"]
        reasoning_len = r["intent_raw"]["reasoning_content_length"]
        sql = r.get("parsed_sql", "N/A")
        print(f"\n{cid}: intent={intent}, content_len={content_len}, reasoning_len={reasoning_len}")
        if sql:
            print(f"  sql: {sql[:100]}")

    # Save
    output_path = Path(__file__).parent.parent / "reports" / "debug_system_failures_v2.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n详细结果已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
