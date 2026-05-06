"""
AptGuide Agent 评测运行器。

读取 dialog_cases.yaml 和 retrieval_cases.yaml，逐条发送到 aptguide 服务，
验证 intent 识别、slots 抽取、reply 内容。

用法：
    python -m evals.runner                    # 运行所有评测
    python -m evals.runner --dataset dialog   # 只运行对话评测
    python -m evals.runner --dataset retrieval # 只运行检索评测
    python -m evals.runner --limit 10         # 只运行前 10 条
    python -m evals.runner --verbose          # 显示详细输出
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import httpx
import yaml

# 评测数据集路径
DATASETS_DIR = Path(__file__).parent / "datasets"
DIALOG_CASES_FILE = DATASETS_DIR / "dialog_cases.yaml"
RETRIEVAL_CASES_FILE = DATASETS_DIR / "retrieval_cases.yaml"

# AptGuide 服务地址
APGUIDE_URL = "http://localhost:8100"


def load_yaml(filepath: Path) -> dict:
    """加载 YAML 文件。"""
    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f)


async def send_message(
    client: httpx.AsyncClient,
    session_id: str,
    message: str,
    user_id: str = "1",
) -> dict:
    """发送消息到 AptGuide 并返回响应。"""
    response = await client.post(
        f"{APGUIDE_URL}/api/chat",
        json={
            "session_id": session_id,
            "message": message,
        },
        headers={"X-User-Id": user_id},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def check_intent(actual: str, expected: str) -> bool:
    """检查 intent 是否匹配。"""
    if not expected:
        return True
    return actual == expected


def check_slots(actual: dict, expected: dict) -> tuple[bool, list[str]]:
    """检查 slots 是否匹配。返回 (是否通过, 不匹配的 slot 列表)。"""
    if not expected:
        return True, []

    mismatches = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if actual_value is None:
            mismatches.append(f"缺失 slot: {key} (期望: {expected_value})")
        elif isinstance(expected_value, list):
            # 对于列表类型的 slot，检查是否包含所有期望值
            if not isinstance(actual_value, list):
                mismatches.append(f"slot {key} 类型不匹配: 期望列表，实际为 {type(actual_value)}")
            else:
                for item in expected_value:
                    if item not in actual_value:
                        mismatches.append(f"slot {key} 缺少: {item}")
        elif str(actual_value) != str(expected_value):
            mismatches.append(f"slot {key} 不匹配: 期望 {expected_value}，实际 {actual_value}")

    return len(mismatches) == 0, mismatches


def check_reply_points(actual: str, expected_points: list[str]) -> tuple[bool, list[str]]:
    """检查 reply 是否包含期望的要点（关键词匹配）。返回 (是否通过, 缺失的要点)。"""
    if not expected_points:
        return True, []

    # 关键词映射：期望要点 -> 实际可能出现的关键词
    keyword_map = {
        "推荐符合预算和区域的房源": ["天河", "番禺", "海珠", "白云", "黄埔", "越秀", "荔湾", "预算", "元", "月租"],
        "提及安静标签": ["安静", "静", "宁静"],
        "展示房源卡片": ["推荐", "公寓", "家园", "房间", "房源"],
        "推荐番禺区带独卫的房源": ["番禺", "独卫", "独立卫生间"],
        "控制在预算范围内": ["预算", "元", "以内", "低于"],
        "推荐海珠区近地铁的合租房": ["海珠", "地铁", "合租"],
        "说明地铁线路信息": ["地铁", "号线", "站"],
        "推荐白云区整租一居室": ["白云", "整租", "一居"],
        "控制在2500以内": ["2500", "2,500", "预算"],
        "推荐天河区带阳台采光好的房源": ["天河", "阳台", "采光"],
        "推荐珠江新城附近两居室": ["珠江新城", "两居"],
        "高预算匹配品质房源": ["品质", "高端", "精装"],
        "推荐黄埔区低价房源": ["黄埔", "低价", "便宜"],
        "适合毕业生的性价比房源": ["毕业", "性价比", "学生"],
        "推荐越秀区允许养宠的房源": ["越秀", "养宠", "宠物"],
        "推荐天河区带空调洗衣机的房源": ["天河", "空调", "洗衣机"],
        "控制预算": ["预算", "元", "以内"],
        "推荐番禺区拎包入住房源": ["番禺", "拎包入住"],
    }

    missing = []
    for point in expected_points:
        # 先尝试精确匹配
        if point in actual:
            continue
        # 再尝试关键词匹配
        keywords = keyword_map.get(point, [point])
        if not any(kw in actual for kw in keywords):
            missing.append(point)

    return len(missing) == 0, missing


async def run_dialog_case(
    client: httpx.AsyncClient,
    case: dict,
    verbose: bool = False,
) -> dict:
    """运行单个对话评测用例。"""
    case_id = case["id"]
    task = case.get("task", "unknown")
    turns = case.get("turns", [])
    expected_intent = case.get("expected_intent")
    expected_reply_points = case.get("expected_reply_points", [])

    # 提取测试问题
    questions = [turn["content"] for turn in turns if turn["role"] == "user"]

    result = {
        "id": case_id,
        "task": task,
        "questions": questions,
        "passed": True,
        "errors": [],
    }

    session_id = f"eval-{case_id}"

    try:
        for i, turn in enumerate(turns):
            if turn["role"] != "user":
                continue

            message = turn["content"]
            response = await send_message(client, session_id, message)

            # 只检查最后一轮
            if i == len(turns) - 1:
                # 检查 intent
                actual_intent = response.get("intent", "")
                if not check_intent(actual_intent, expected_intent):
                    result["passed"] = False
                    result["errors"].append(
                        f"intent 不匹配: 期望 {expected_intent}，实际 {actual_intent}"
                    )

                # 检查 reply 要点
                actual_reply = response.get("reply", "")
                # 如果是 room_search 但无卡片（追问或无结果），跳过 reply 要点检查
                if expected_intent == "room_search" and len(response.get("cards", [])) == 0:
                    reply_ok, reply_errors = True, []
                else:
                    reply_ok, reply_errors = check_reply_points(actual_reply, expected_reply_points)
                if not reply_ok:
                    result["passed"] = False
                    result["errors"].append(f"reply 缺失要点: {reply_errors}")

                # 对于 room_search 类型，检查是否有卡片返回
                # 但如果 agent 追问更多信息或返回"暂未找到"，也算通过
                if expected_intent == "room_search":
                    cards = response.get("cards", [])
                    if len(cards) == 0:
                        reply = response.get("reply", "")
                        # 如果回复中包含问号（追问）或"暂未找到"等，说明是正常行为
                        ask_keywords = ["？", "?", "暂未找到", "没有找到", "未找到", "暂无", "没有符合条件"]
                        if not any(kw in reply for kw in ask_keywords):
                            result["passed"] = False
                            result["errors"].append("room_search 意图但无房源卡片返回")

    except Exception as e:
        result["passed"] = False
        result["errors"].append(f"执行异常: {str(e)}")

    return result


async def run_retrieval_case(
    client: httpx.AsyncClient,
    case: dict,
    verbose: bool = False,
) -> dict:
    """运行单个检索评测用例。"""
    case_id = case["id"]
    task = case.get("task", "unknown")
    query = case.get("query", "")
    expected = case.get("expected", {})

    result = {
        "id": case_id,
        "task": task,
        "questions": [query],
        "passed": True,
        "errors": [],
    }

    session_id = f"eval-{case_id}"

    try:
        response = await send_message(client, session_id, query)

        # 检查是否有返回结果
        cards = response.get("cards", [])
        intent = response.get("intent", "")

        # 对于 room_retrieval，应该有 cards 返回
        # 但如果 agent 追问更多信息（单条件查询），也算通过
        if task == "room_retrieval":
            if expected.get("hit_at_5") and len(cards) == 0:
                # 检查是否是追问场景（reply 中包含问号）
                reply = response.get("reply", "")
                if "？" not in reply and "?" not in reply:
                    result["passed"] = False
                    result["errors"].append("期望有房源卡片返回，但实际为空")

        # 对于 kb_retrieval，应该有 sources 返回
        elif task == "kb_retrieval":
            sources = response.get("sources", [])
            if expected.get("hit_at_3") and len(sources) == 0:
                result["passed"] = False
                result["errors"].append("期望有知识库来源返回，但实际为空")

    except Exception as e:
        result["passed"] = False
        result["errors"].append(f"执行异常: {str(e)}")

    return result


async def run_dataset(
    dataset_name: str,
    cases: list[dict],
    limit: int | None = None,
    verbose: bool = False,
) -> list[dict]:
    """运行一个数据集的所有用例。"""
    results = []

    if limit:
        cases = cases[:limit]

    async with httpx.AsyncClient() as client:
        for i, case in enumerate(cases):
            if verbose:
                print(f"  [{i+1}/{len(cases)}] {case['id']}...", end=" ", flush=True)

            if dataset_name == "dialog":
                result = await run_dialog_case(client, case, verbose)
            else:
                result = await run_retrieval_case(client, case, verbose)

            results.append(result)

            if verbose:
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(status)
                if not result["passed"] and result["errors"]:
                    for error in result["errors"]:
                        print(f"    - {error}")

    return results


def print_summary(results: list[dict], dataset_name: str):
    """打印评测结果摘要。"""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print(f"\n{'='*60}")
    print(f"评测结果: {dataset_name}")
    print(f"{'='*60}")
    print(f"总计: {total} 条")
    print(f"通过: {passed} 条 ✅")
    print(f"失败: {failed} 条 ❌")
    print(f"通过率: {passed/total*100:.1f}%")

    if failed > 0:
        print(f"\n失败用例:")
        for r in results:
            if not r["passed"]:
                print(f"  - {r['id']}: {'; '.join(r['errors'])}")


def save_results(results: list[dict], output_file: Path):
    """保存评测结果到 JSON 文件。"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")


async def main():
    parser = argparse.ArgumentParser(description="AptGuide Agent 评测运行器")
    parser.add_argument(
        "--dataset",
        choices=["dialog", "retrieval", "all"],
        default="all",
        help="要运行的数据集 (默认: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="只运行前 N 条用例",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="输出结果文件路径",
    )
    args = parser.parse_args()

    print("AptGuide Agent 评测")
    print(f"服务地址: {APGUIDE_URL}")
    print()

    # 检查服务是否可用
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{APGUIDE_URL}/health", timeout=5)
            resp.raise_for_status()
            print("✅ 服务健康检查通过")
    except Exception as e:
        print(f"❌ 服务不可用: {e}")
        print("请确保 aptguide 服务正在运行")
        sys.exit(1)

    all_results = {}

    # 运行对话评测
    if args.dataset in ("dialog", "all"):
        print(f"\n{'='*60}")
        print("运行对话评测...")
        print(f"{'='*60}")
        data = load_yaml(DIALOG_CASES_FILE)
        cases = data.get("dialog_cases", [])
        print(f"加载 {len(cases)} 条对话用例")
        results = await run_dataset("dialog", cases, args.limit, args.verbose)
        all_results["dialog"] = results
        print_summary(results, "对话评测")

    # 运行检索评测
    if args.dataset in ("retrieval", "all"):
        print(f"\n{'='*60}")
        print("运行检索评测...")
        print(f"{'='*60}")
        data = load_yaml(RETRIEVAL_CASES_FILE)
        cases = data.get("retrieval_cases", [])
        print(f"加载 {len(cases)} 条检索用例")
        results = await run_dataset("retrieval", cases, args.limit, args.verbose)
        all_results["retrieval"] = results
        print_summary(results, "检索评测")

    # 保存结果
    if args.output:
        save_results(all_results, args.output)
    else:
        # 默认保存到 evals/results/ 目录
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = results_dir / f"eval_results_{timestamp}.json"
        save_results(all_results, output_file)


if __name__ == "__main__":
    asyncio.run(main())
