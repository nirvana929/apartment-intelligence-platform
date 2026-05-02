from aptguide.agent.state import AgentState
from aptguide.vector.kb_search import KBSearch


async def kb_search_node(state: AgentState, kb: KBSearch) -> dict:
    """知识检索节点。"""
    results = await kb.search(state["message"], top_k=3)

    search_results = []
    sources = []
    for result in results:
        search_results.append(result)
        sources.append(result["id"])

    return {
        "search_results": search_results,
        "sources": sources,
    }
