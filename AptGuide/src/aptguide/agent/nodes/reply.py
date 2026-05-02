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
    """回复生成节点。"""
    if not state["search_results"]:
        return {
            "reply": "抱歉，我暂时无法回答这个问题。建议联系门店咨询。",
            "cards": [],
            "actions": [],
        }

    # 格式化检索结果
    results_text = "\n".join([
        f"- {r['title']}: {r['content']}"
        for r in state["search_results"]
    ])

    prompt = REPLY_PROMPT.format(
        message=state["message"],
        search_results=results_text,
    )
    reply = await llm.generate(prompt)

    return {
        "reply": reply,
        "cards": [],
        "actions": [],
    }
