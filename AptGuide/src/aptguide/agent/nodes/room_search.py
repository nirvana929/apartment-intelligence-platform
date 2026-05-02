from aptguide.agent.state import AgentState
from aptguide.vector.room_index import RoomIndex


async def room_search_node(state: AgentState, room_index: RoomIndex) -> dict:
    """房源召回节点。"""
    slots = state["slots"]

    # 构建查询
    query_parts = []
    if slots.get("tags"):
        query_parts.extend(slots["tags"])
    if slots.get("district"):
        query_parts.append(slots["district"])

    query = " ".join(query_parts) if query_parts else state["message"]

    # 检索房源
    rooms = await room_index.search(
        query=query,
        max_rent=slots.get("max_rent"),
        district=slots.get("district"),
    )

    return {"search_results": rooms}
