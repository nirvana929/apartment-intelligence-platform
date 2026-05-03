from aptguide.agent.state import AgentState
from aptguide.core.logging import get_logger
from aptguide.vector.room_index import RoomIndex

logger = get_logger(__name__)


async def room_search_node(state: AgentState, room_index: RoomIndex) -> dict:
    """房源召回节点。"""
    slots = state["slots"]

    query_parts = []
    if slots.get("tags"):
        query_parts.extend(slots["tags"])
    if slots.get("district"):
        query_parts.append(slots["district"])

    query = " ".join(query_parts) if query_parts else state["message"]

    try:
        rooms = await room_index.search(
            query=query,
            max_rent=slots.get("max_rent"),
            district=slots.get("district"),
        )
    except Exception as e:
        logger.error("room_search failed: %s", str(e))
        rooms = []

    return {"search_results": rooms}
