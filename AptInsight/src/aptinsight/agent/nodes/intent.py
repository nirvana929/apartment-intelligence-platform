"""
意图识别节点模块

本模块负责识别用户问题的意图类型，是 LangGraph 工作流的第一个节点。

学习要点：
1. 节点函数 - LangGraph 中的处理单元
2. LLM 调用 - 使用大语言模型进行意图分类
3. 提示词工程 - 如何设计有效的提示词
4. 状态更新 - 如何更新 LangGraph 状态

意图类型：
- analysis: 业务分析问题，需要查询数据库
- chitchat: 闲聊问题，不需要查询
- out_of_scope: 超出范围的问题，无法处理

工作流程：
用户问题 → 读取问题 → 调用 LLM 分类 → 更新状态 → 返回
"""

from __future__ import annotations

import json

from ...core.logging import get_logger
from ...llm.client import LLMClient
from ..state import (
    AgentState,
    INTENT_ANALYSIS,
    INTENT_CHITCHAT,
    INTENT_OUT_OF_SCOPE,
)

# 获取日志记录器
# 学习要点：使用结构化日志记录关键操作
logger = get_logger(__name__)


# ============================================================================
# 意图识别提示词
# ============================================================================

# 学习要点：提示词是 LLM 应用的核心
# 好的提示词应该：
# 1. 清晰说明任务
# 2. 提供分类标准
# 3. 给出示例
# 4. 指定输出格式

INTENT_PROMPT = """你是一个公寓运营分析助手的意图分类器。
你的任务是判断用户问题属于哪种类型。

## 分类标准

### analysis（业务分析）
需要查询数据库才能回答的运营分析问题，例如：
- 公寓信息查询（名称、地址、房间数等）
- 租约统计（签约量、退租量、有效租约等）
- 预约分析（预约量、看房完成率等）
- 租金分析（平均租金、租金趋势等）
- 浏览热度分析（浏览量、热门房间等）

示例：
- "本月各公寓预约量是多少？"
- "最近6个月新增租约趋势如何？"
- "哪些公寓的预约量高但签约量低？"
- "当前有多少有效租约？"
- "租金最高的公寓是哪个？"

### chitchat（闲聊）
不涉及业务数据的普通对话，例如：
- 打招呼（你好、早上好等）
- 询问系统功能（你能做什么？）
- 一般性问题（天气、时间等）
- 表达感谢或告别

示例：
- "你好"
- "你是谁？"
- "谢谢"
- "今天天气怎么样？"

### out_of_scope（超出范围）
无法处理或不应该处理的问题，例如：
- 涉及个人隐私的问题（查询某人的手机号、身份证号等）
- 需要写操作的问题（修改数据、删除记录等）
- 超出公寓运营范围的问题（股票、游戏等）
- 涉及敏感信息的问题

示例：
- "帮我查一下张三的手机号"
- "删除所有过期租约"
- "最近股市怎么样？"
- "帮我修改一下这个公寓的信息"

## 输出要求

请以 JSON 格式输出，包含以下字段：
- intent: 意图类型（analysis/chitchat/out_of_scope）
- reason: 分类理由（简要说明为什么这样分类）

示例输出：
{{"intent": "analysis", "reason": "用户询问预约量统计，需要查询数据库"}}

## 用户问题

{question}"""


# ============================================================================
# 意图识别节点函数
# ============================================================================

async def classify_intent(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    意图识别节点

    这是 LangGraph 工作流的第一个节点，负责：
    1. 读取用户问题
    2. 调用 LLM 进行意图分类
    3. 更新状态中的意图字段

    Args:
        state: 当前状态
        llm_client: LLM 客户端实例

    Returns:
        更新后的状态

    学习要点：
    - 节点函数签名：接收状态，返回更新后的状态
    - 异步函数：使用 async/await 进行异步操作
    - 错误处理：使用 try/except 捕获异常
    """
    # 读取用户问题
    question = state.get("question", "")

    # 如果问题为空，走 out_of_scope 路径（不设 error，避免跳过 write_answer）
    if not question.strip():
        logger.warning("用户问题为空")
        return {
            **state,
            "intent": INTENT_OUT_OF_SCOPE,
        }

    logger.info(f"开始意图识别，问题: {question[:50]}")

    try:
        # 构造提示词
        logger.info("构造意图识别提示词")
        prompt = INTENT_PROMPT.format(question=question)

        # 调用 LLM 进行分类
        logger.info("调用 LLM 进行意图分类")
        response = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        # 记录 LLM 原始响应用于调试
        logger.info(f"意图识别 LLM 原始响应: {response[:200]}")

        # 解析 LLM 响应
        result = _parse_intent_response(response)

        intent = result.get("intent", INTENT_OUT_OF_SCOPE)
        reason = result.get("reason", "未提供理由")

        logger.info(f"意图识别完成，意图: {intent}，理由: {reason[:50]}")

        # 更新状态
        return {
            **state,
            "intent": intent,
            "normalized_question": question,
        }

    except Exception as e:
        logger.error(f"意图识别失败，错误: {e}，类型: {type(e).__name__}")
        # 不设 error，走 out_of_scope 路径到 write_answer，由 failure.py 归类
        return {
            **state,
            "intent": INTENT_OUT_OF_SCOPE,
            "error": f"意图识别失败: {str(e)}",
        }


def _parse_intent_response(response: str) -> dict[str, str]:
    """
    解析 LLM 的意图识别响应

    Args:
        response: LLM 的原始响应文本

    Returns:
        解析后的结果字典，包含 intent 和 reason

    学习要点：
    - JSON 解析：从 LLM 响应中提取 JSON 数据
    - 错误处理：处理解析失败的情况
    - 默认值：为缺失字段提供默认值
    """
    try:
        # 尝试从响应中提取 JSON
        # LLM 可能在 JSON 前后添加了其他文本
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("响应中没有找到 JSON")

        json_str = response[json_start:json_end]
        result = json.loads(json_str)

        # 验证意图类型
        valid_intents = {INTENT_ANALYSIS, INTENT_CHITCHAT, INTENT_OUT_OF_SCOPE}
        intent = result.get("intent", "")

        if intent not in valid_intents:
            logger.warning(f"无效的意图类型: {intent}，使用默认值")
            intent = INTENT_OUT_OF_SCOPE

        return {
            "intent": intent,
            "reason": result.get("reason", "未提供理由"),
        }

    except (json.JSONDecodeError, ValueError) as e:
        # JSON 解析失败，使用默认值
        logger.warning(f"解析意图响应失败: {e}")

        # 尝试从文本中推断意图
        response_lower = response.lower()
        if "analysis" in response_lower or "分析" in response_lower:
            intent = INTENT_ANALYSIS
        elif "chitchat" in response_lower or "闲聊" in response_lower:
            intent = INTENT_CHITCHAT
        else:
            intent = INTENT_OUT_OF_SCOPE

        return {
            "intent": intent,
            "reason": "从文本推断意图（JSON解析失败）",
        }


# ============================================================================
# 辅助函数
# ============================================================================

def is_analysis_question(question: str) -> bool:
    """
    快速判断是否为业务分析问题（基于关键词）

    这是一个轻量级的判断，不调用 LLM，用于快速过滤。

    Args:
        question: 用户问题

    Returns:
        True 如果可能是业务分析问题，否则 False

    学习要点：
    - 关键词匹配：快速但不够精确的方法
    - 作为 LLM 分类的补充，提高响应速度
    """
    analysis_keywords = [
        "公寓", "房间", "租约", "预约", "租金",
        "浏览", "签约", "退租", "空置", "统计",
        "多少", "几个", "哪些", "趋势", "排行",
    ]

    question_lower = question.lower()
    return any(keyword in question_lower for keyword in analysis_keywords)


def is_chitchat_question(question: str) -> bool:
    """
    快速判断是否为闲聊问题（基于关键词）

    Args:
        question: 用户问题

    Returns:
        True 如果是闲聊问题，否则 False
    """
    chitchat_keywords = [
        "你好", "早上好", "下午好", "晚上好",
        "谢谢", "感谢", "再见", "拜拜",
        "你是谁", "你能做什么", "帮助",
    ]

    question_lower = question.lower()
    return any(keyword in question_lower for keyword in chitchat_keywords)
