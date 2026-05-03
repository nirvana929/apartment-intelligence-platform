from aptguide.agent.state import AgentState
from aptguide.core.logging import get_logger
from aptguide.vector.kb_search import KBSearch

logger = get_logger(__name__)


async def kb_search_node(state: AgentState, kb: KBSearch) -> dict:
    """知识检索节点。"""
    try:
        results = await kb.search(state["message"], top_k=3)
    except Exception as e:
        logger.error("kb_search failed: %s", str(e))
        results = []

    search_results = []
    sources = []
    for result in results:
        search_results.append(result)
        sources.append(result["id"])

    return {
        "search_results": search_results,
        "sources": sources,
    }
