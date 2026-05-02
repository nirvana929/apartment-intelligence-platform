from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient

ASK_PROMPT = """你是一个租房助手。用户的需求信息不完整，需要追问缺失的槽位。

当前槽位：{slots}
缺失槽位：{missing_slots}

请生成一个友好的追问，询问缺失的信息。"""


def get_missing_slots(slots: dict) -> list[str]:
    """获取缺失的槽位。"""
    missing = []
    if not slots.get("max_rent"):
        missing.append("预算")
    if not slots.get("district"):
        missing.append("区域")
    return missing


async def ask_node(state: AgentState, llm: LLMClient) -> dict:
    """追问生成节点。"""
    missing = get_missing_slots(state["slots"])

    if not missing:
        # 槽位充足，不需要追问
        return {"reply": ""}

    prompt = ASK_PROMPT.format(
        slots=state["slots"],
        missing_slots=", ".join(missing),
    )

    reply = await llm.generate(prompt)
    return {"reply": reply}
