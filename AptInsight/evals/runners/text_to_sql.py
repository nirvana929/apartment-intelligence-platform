"""
Text-to-SQL 评测运行器

本模块实现了 Text-to-SQL 的评测系统，用于评估 Agent 的性能。

学习要点：
1. 评测系统设计 - 如何设计有效的评测系统
2. 测试用例管理 - 如何管理和组织测试用例
3. 结果评估 - 如何评估生成的 SQL 质量
4. 报告生成 - 如何生成评测报告

评测维度：
1. 意图识别准确率
2. SQL 生成准确率
3. 安全检查通过率
4. 执行成功率
5. 答案质量

使用示例：
    python -m evals.runners.text_to_sql --cases evals/datasets/text_to_sql_cases.yaml
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aptinsight.agent import AgentExecutor, run_agent
from aptinsight.core.config import get_settings
from aptinsight.core.logging import get_logger
from aptinsight.llm.client import LLMClient

# 获取日志记录器
logger = get_logger(__name__)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class TestCase:
    """
    测试用例

    学习要点：
    - 数据类：使用 @dataclass 定义数据结构
    - 类型提示：为字段添加类型提示
    """
    id: str                                    # 测试用例 ID
    category: str                              # 测试类别
    question: str                              # 用户问题
    expected: dict[str, Any] = field(default_factory=dict)  # 期望结果


@dataclass
class TestResult:
    """
    测试结果

    学习要点：
    - 结果封装：将测试结果封装成对象
    - 状态管理：跟踪测试的各个阶段
    """
    test_id: str                               # 测试用例 ID
    passed: bool = False                       # 是否通过
    error: str | None = None                   # 错误信息
    actual_intent: str = ""                    # 实际识别的意图
    actual_sql: str = ""                       # 实际生成的 SQL
    guard_passed: bool = False                 # SQL 守卫是否通过
    execution_success: bool = False            # SQL 执行是否成功
    answer: str = ""                           # 生成的答案
    processing_time_ms: float = 0.0            # 处理耗时（毫秒）
    details: dict[str, Any] = field(default_factory=dict)  # 详细信息


@dataclass
class EvalReport:
    """
    评测报告

    学习要点：
    - 报告结构：组织评测结果的结构
    - 统计信息：计算各种统计指标
    """
    total_cases: int = 0                       # 总测试用例数
    passed_cases: int = 0                      # 通过的测试用例数
    failed_cases: int = 0                      # 失败的测试用例数
    error_cases: int = 0                       # 出错的测试用例数
    pass_rate: float = 0.0                     # 通过率
    avg_processing_time_ms: float = 0.0        # 平均处理耗时
    results: list[TestResult] = field(default_factory=list)  # 测试结果列表


# ============================================================================
# 测试用例加载
# ============================================================================

def load_test_cases(file_path: str) -> list[TestCase]:
    """
    加载测试用例

    Args:
        file_path: 测试用例文件路径（YAML 格式）

    Returns:
        测试用例列表

    学习要点：
    - YAML 解析：使用 PyYAML 解析 YAML 文件
    - 数据转换：将字典转换为数据类对象
    - 文件处理：处理文件读取和解析错误
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, list):
            raise ValueError("测试用例文件格式错误，应该是列表")

        test_cases = []
        for item in data:
            test_case = TestCase(
                id=item.get("id", ""),
                category=item.get("category", ""),
                question=item.get("question", ""),
                expected=item.get("expected", {}),
            )
            test_cases.append(test_case)

        logger.info(f"加载了 {len(test_cases)} 个测试用例")
        return test_cases

    except Exception as e:
        logger.error(f"加载测试用例失败: {e}")
        return []


# ============================================================================
# 测试执行
# ============================================================================

async def run_single_test(
    test_case: TestCase,
    agent_executor: AgentExecutor,
    llm_client: LLMClient,
) -> TestResult:
    """
    执行单个测试用例

    Args:
        test_case: 测试用例
        agent_executor: Agent 执行器
        llm_client: LLM 客户端

    Returns:
        测试结果

    学习要点：
    - 异步执行：使用 async/await 处理异步操作
    - 错误处理：捕获和处理各种异常
    - 结果验证：验证实际结果是否符合预期
    """
    logger.info(f"执行测试用例: {test_case.id} - {test_case.question[:50]}")

    start_time = time.monotonic()
    result = TestResult(test_id=test_case.id)

    try:
        # 执行 Agent 工作流
        agent_result = await run_agent(
            question=test_case.question,
            llm_client=llm_client,
        )

        # 计算处理时间
        result.processing_time_ms = (time.monotonic() - start_time) * 1000

        # 提取实际结果
        result.actual_intent = agent_result.get("intent", "")
        result.actual_sql = agent_result.get("sql", "")
        result.guard_passed = not bool(agent_result.get("error"))
        result.execution_success = bool(agent_result.get("rows"))
        result.answer = agent_result.get("answer", "")

        # 验证结果
        result.passed = _validate_result(test_case.expected, agent_result)
        result.details = {
            "expected": test_case.expected,
            "actual": agent_result,
        }

        if result.passed:
            logger.info(f"测试用例 {test_case.id} 通过")
        else:
            logger.warning(f"测试用例 {test_case.id} 失败")

    except Exception as e:
        result.processing_time_ms = (time.monotonic() - start_time) * 1000
        result.error = str(e)
        logger.error(f"测试用例 {test_case.id} 执行出错: {e}")

    return result


def _validate_result(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    """
    验证测试结果

    Args:
        expected: 期望结果
        actual: 实际结果

    Returns:
        True 如果结果符合预期，否则 False

    学习要点：
    - 结果验证：比较实际结果和期望结果
    - 多维度验证：从多个维度验证结果
    """
    # 检查是否应该拒绝
    if expected.get("must_reject"):
        # 如果应该拒绝，检查是否有错误或 SQL 守卫失败
        if actual.get("error"):
            return True
        guard_result = actual.get("sql_guard_result", {})
        if not guard_result.get("passed", True):
            return True
        # 检查是否被识别为超出范围或闲聊
        intent = actual.get("intent", "")
        if intent in ["out_of_scope", "chitchat"]:
            return True
        return False

    # 检查 SQL 是否包含禁止的关键字（使用单词边界匹配，避免误判字段名如 is_deleted）
    import re
    forbidden = expected.get("forbidden", [])
    actual_sql = (actual.get("sql") or "").upper()
    for keyword in forbidden:
        pattern = r'\b' + keyword.upper() + r'\b'
        if re.search(pattern, actual_sql):
            return False

    # 检查是否使用了必须的表
    must_use_tables = expected.get("must_use_tables", [])
    actual_sql_lower = (actual.get("sql") or "").lower()
    for table in must_use_tables:
        if table.lower() not in actual_sql_lower:
            return False

    # 检查是否包含必须的关键字
    must_contain = expected.get("must_contain", [])
    for keyword in must_contain:
        if keyword.upper() not in actual_sql:
            return False

    # 检查图表类型（如果期望中指定了）
    expected_chart_type = expected.get("chart_type")
    if expected_chart_type:
        actual_chart_type = actual.get("chart_type")
        if actual_chart_type != expected_chart_type:
            logger.warning(
                f"图表类型不匹配: 期望 {expected_chart_type}，实际 {actual_chart_type}"
            )
            return False

    return True


# ============================================================================
# 批量测试执行
# ============================================================================

async def run_eval(
    test_cases: list[TestCase],
    agent_executor: AgentExecutor,
    llm_client: LLMClient,
    max_concurrent: int = 3,
) -> EvalReport:
    """
    执行批量评测

    Args:
        test_cases: 测试用例列表
        agent_executor: Agent 执行器
        llm_client: LLM 客户端
        max_concurrent: 最大并发数

    Returns:
        评测报告

    学习要点：
    - 并发控制：使用信号量控制并发数量
    - 批量处理：处理多个测试用例
    - 结果聚合：聚合所有测试结果
    """
    logger.info(f"开始执行评测，共 {len(test_cases)} 个测试用例")

    # 创建信号量控制并发
    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_with_semaphore(test_case: TestCase) -> TestResult:
        """带信号量的测试执行"""
        async with semaphore:
            return await run_single_test(test_case, agent_executor, llm_client)

    # 并发执行所有测试
    tasks = [run_with_semaphore(tc) for tc in test_cases]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    test_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # 处理异常情况
            test_results.append(TestResult(
                test_id=test_cases[i].id,
                error=str(result),
            ))
        else:
            test_results.append(result)

    # 生成报告
    report = _generate_report(test_results)

    logger.info(
        f"评测完成: 通过 {report.passed_cases}/{report.total_cases} "
        f"({report.pass_rate:.1%})"
    )

    return report


def _generate_report(results: list[TestResult]) -> EvalReport:
    """
    生成评测报告

    Args:
        results: 测试结果列表

    Returns:
        评测报告

    学习要点：
    - 统计计算：计算各种统计指标
    - 报告生成：组织评测结果
    """
    report = EvalReport()
    report.total_cases = len(results)
    report.results = results

    passed_count = 0
    failed_count = 0
    error_count = 0
    total_time = 0.0

    for result in results:
        if result.error:
            error_count += 1
        elif result.passed:
            passed_count += 1
        else:
            failed_count += 1

        total_time += result.processing_time_ms

    report.passed_cases = passed_count
    report.failed_cases = failed_count
    report.error_cases = error_count
    report.pass_rate = passed_count / report.total_cases if report.total_cases > 0 else 0.0
    report.avg_processing_time_ms = total_time / report.total_cases if report.total_cases > 0 else 0.0

    return report


# ============================================================================
# 报告输出
# ============================================================================

def print_report(report: EvalReport) -> None:
    """
    打印评测报告

    Args:
        report: 评测报告

    学习要点：
    - 格式化输出：使用表格形式展示结果
    - 颜色输出：使用颜色区分通过和失败
    """
    print("\n" + "=" * 60)
    print("AptInsight Text-to-SQL 评测报告")
    print("=" * 60)

    print(f"\n总测试用例数: {report.total_cases}")
    print(f"通过: {report.passed_cases}")
    print(f"失败: {report.failed_cases}")
    print(f"出错: {report.error_cases}")
    print(f"通过率: {report.pass_rate:.1%}")
    print(f"平均处理时间: {report.avg_processing_time_ms:.2f} ms")

    print("\n" + "-" * 60)
    print("详细结果:")
    print("-" * 60)

    for result in report.results:
        status = "✓" if result.passed else "✗"
        if result.error:
            status = "⚠"

        print(f"\n[{status}] 测试用例 {result.test_id}")
        print(f"  处理时间: {result.processing_time_ms:.2f} ms")

        if result.error:
            print(f"  错误: {result.error}")
        elif not result.passed:
            print("  失败原因: 结果不符合预期")

    print("\n" + "=" * 60)


def save_report(report: EvalReport, output_path: str) -> None:
    """
    保存评测报告到文件

    Args:
        report: 评测报告
        output_path: 输出文件路径

    学习要点：
    - JSON 序列化：将数据类转换为 JSON 格式
    - 文件写入：保存报告到文件
    """
    report_data = {
        "summary": {
            "total_cases": report.total_cases,
            "passed_cases": report.passed_cases,
            "failed_cases": report.failed_cases,
            "error_cases": report.error_cases,
            "pass_rate": report.pass_rate,
            "avg_processing_time_ms": report.avg_processing_time_ms,
        },
        "results": [
            {
                "test_id": r.test_id,
                "passed": r.passed,
                "error": r.error,
                "actual_intent": r.actual_intent,
                "actual_sql": r.actual_sql,
                "guard_passed": r.guard_passed,
                "execution_success": r.execution_success,
                "processing_time_ms": r.processing_time_ms,
            }
            for r in report.results
        ],
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info(f"评测报告已保存到: {output_path}")
    except Exception as e:
        logger.error(f"保存评测报告失败: {e}")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """
    主函数

    学习要点：
    - 命令行参数解析：使用 argparse 解析命令行参数
    - 异步主函数：使用 asyncio.run() 运行异步主函数
    """
    import argparse

    parser = argparse.ArgumentParser(description="AptInsight Text-to-SQL 评测器")
    parser.add_argument(
        "--cases",
        type=str,
        default="evals/datasets/text_to_sql_cases.yaml",
        help="测试用例文件路径",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evals/reports/eval_report.json",
        help="评测报告输出路径",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="最大并发数",
    )

    args = parser.parse_args()

    # 加载测试用例
    test_cases = load_test_cases(args.cases)
    if not test_cases:
        logger.error("没有加载到测试用例")
        return

    # 创建 LLM 客户端和 Agent 执行器
    settings = get_settings()
    llm_client = LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
    agent_executor = AgentExecutor(llm_client)

    # 执行评测
    report = await run_eval(
        test_cases=test_cases,
        agent_executor=agent_executor,
        llm_client=llm_client,
        max_concurrent=args.max_concurrent,
    )

    # 打印报告
    print_report(report)

    # 保存报告
    save_report(report, args.output)


if __name__ == "__main__":
    asyncio.run(main())
