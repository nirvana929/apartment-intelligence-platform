"""
重排与推荐理由生成节点 —— 把检索结果转化为用户友好的推荐。

【学习要点】
1. RAG 的"R"（Retrieval）和"G"（Generation）的衔接点：
   - 检索结果（search_results）是从 Milvus 拿到的原始数据
   - 这个节点负责"包装"：生成推荐理由 + 构建前端卡片
2. Pydantic 模型（Card, Action）用于数据校验：
   - Card 和 Action 是预定义的数据结构
   - model_dump() 把 Pydantic 对象转成普通 dict（JSON 可序列化）
3. 每个房源同时生成两种操作按钮：查看详情 + 预约看房
"""

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.schemas.response import Action, Card

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
    """
    推荐理由生成节点。

    流程：
    1. 检查是否有搜索结果
    2. 把房源信息格式化为文本，填入提示词
    3. 让 LLM 生成推荐理由
    4. 构建前端卡片和操作按钮
    """
    if not state["search_results"]:
        return {
            "reply": "抱歉，暂未找到符合条件的房源。你可以尝试调整预算或区域。",
            "cards": [],
            "actions": [],
        }

    # 格式化房源信息 —— 把结构化数据转为 LLM 能理解的文本
    rooms_text = "\n".join(
        [
            f"- {r['title']}：月租 {r['rent']}，{', '.join(r['tags'])}，{r['description']}"
            for r in state["search_results"]
        ]
    )

    prompt = RERANK_PROMPT.format(
        message=state["message"],
        slots=state["slots"],
        rooms=rooms_text,
    )

    # 让 LLM 生成推荐理由（如"这套房子符合您的预算，且靠近地铁站"）
    reply = await llm.generate(prompt)

    # 构建卡片和操作按钮
    cards = []
    actions = []
    for room in state["search_results"]:
        # Card 是 Pydantic 模型，会自动校验字段类型
        cards.append(
            Card(
                type="room",
                room_id=room["room_id"],
                title=room["title"],
                rent=room["rent"],
                district=room["district"],
                tags=room["tags"],
                description=room["description"],
            )
        )
        # 每个房源两个操作按钮
        actions.append(Action(type="view_detail", room_id=room["room_id"]))
        actions.append(Action(type="create_appointment", room_id=room["room_id"]))

    # model_dump() 把 Pydantic 对象转成普通 dict（JSON 可序列化）
    return {
        "reply": reply,
        "cards": [card.model_dump() for card in cards],
        "actions": [action.model_dump() for action in actions],
    }
