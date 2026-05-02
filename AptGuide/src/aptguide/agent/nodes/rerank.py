from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.schemas.response import Card, Action


RERANK_PROMPT = """你是一个租房助手。根据用户需求和检索到的房源，生成推荐理由。

用户需求：{message}
用户槽位：{slots}

房源列表：
{rooms}

请生成：
1. 自然语言推荐理由（简洁明了）
2. 突出房源与用户需求的匹配点

只返回推荐理由，不要返回其他内容。"""


async def rerank_node(state: AgentState, llm: LLMClient) -> dict:
    """推荐理由生成节点。"""
    if not state["search_results"]:
        return {
            "reply": "抱歉，暂未找到符合条件的房源。你可以尝试调整预算或区域。",
            "cards": [],
            "actions": [],
        }

    # 格式化房源信息
    rooms_text = "\n".join([
        f"- {r['title']}：月租 {r['rent']}，{', '.join(r['tags'])}，{r['description']}"
        for r in state["search_results"]
    ])

    prompt = RERANK_PROMPT.format(
        message=state["message"],
        slots=state["slots"],
        rooms=rooms_text,
    )

    reply = await llm.generate(prompt)

    # 构建卡片
    cards = []
    actions = []
    for room in state["search_results"]:
        cards.append(Card(
            type="room",
            room_id=room["room_id"],
            title=room["title"],
            rent=room["rent"],
            district=room["district"],
            tags=room["tags"],
            description=room["description"],
        ))
        actions.append(Action(type="view_detail", room_id=room["room_id"]))
        actions.append(Action(type="create_appointment", room_id=room["room_id"]))

    return {
        "reply": reply,
        "cards": [card.model_dump() for card in cards],
        "actions": [action.model_dump() for action in actions],
    }
