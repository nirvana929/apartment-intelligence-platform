"""
回复生成节点 —— 所有路径的"终点站"。

【学习要点】
1. 终端节点：reply_node 是大多数路径的最后一个节点
2. 透传逻辑：如果前面的节点（如 tool_node、rerank_node）已经生成了回复，
   就直接透传，不重复生成
3. 降级策略：没有检索结果时，给出兜底回复（"联系门店"）
4. confirmation 清理：用户取消操作时，清除 confirmation 状态
"""

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient

REPLY_PROMPT = """你是一个租房助手。根据检索到的知识库内容，回答用户问题。

要求：
1. 回答要简洁明了
2. 如果涉及具体规则，引用来源
3. 如果没有找到相关信息，告知用户联系门店

用户问题：{message}

检索结果：
{search_results}"""


async def reply_node(state: AgentState, llm: LLMClient) -> dict:
    """
    回复生成节点。

    这个节点是"兜底"节点，处理多种情况：
    1. 用户取消确认操作 → 直接返回取消信息
    2. 前面节点已生成回复 → 透传（不重复生成）
    3. 有检索结果 → 让 LLM 基于检索结果生成回复
    4. 没有检索结果 → 返回兜底回复
    """
    msg = state.get("message", "").strip()

    # 情况1：用户取消确认操作
    if state.get("confirmation") and msg in ("取消", "不", "不要", "算了"):
        return {
            "reply": "好的，已取消操作。有其他需要随时告诉我～",
            "cards": [],
            "actions": [],
            "confirmation": None,  # 清除 confirmation 状态
        }

    # 情况2：前面节点已生成回复，直接透传
    # 为什么需要这个判断？
    # 因为 LangGraph 的流程是：tool_node → reply_node
    # tool_node 已经生成了 reply，reply_node 不应该重复生成
    has_reply = bool(state.get("reply"))
    has_cards = bool(state.get("cards"))
    is_tool_intent = state.get("intent") in ("appointment_query", "lease_query", "appointment_create")
    is_tool_result = has_reply and not state.get("search_results") and not state.get("confirmation")

    if has_reply and (has_cards or is_tool_intent or is_tool_result):
        return {
            "reply": state["reply"],
            "cards": state.get("cards", []),
            "actions": state.get("actions", []),
        }

    # 情况3：没有检索结果 → 兜底回复
    if not state["search_results"]:
        return {
            "reply": "抱歉，我暂时无法回答这个问题。建议联系门店咨询。",
            "cards": [],
            "actions": [],
        }

    # 情况4：有检索结果 → 让 LLM 基于检索结果生成回复
    # 把检索结果格式化为文本，填入提示词
    results_text = "\n".join([
        f"- {r.get('title', '')}: {r.get('content') or r.get('description', '')}"
        for r in state["search_results"]
    ])

    prompt = REPLY_PROMPT.format(
        message=state["message"],
        search_results=results_text,
    )
    reply = await llm.generate(prompt)

    return {
        "reply": reply,
        "cards": [],      # 知识库问答不需要卡片
        "actions": [],    # 知识库问答不需要操作按钮
    }
