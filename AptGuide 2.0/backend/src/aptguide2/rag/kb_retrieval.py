"""KB retrieval with multi-recall, source rerank, and confidence gate.

学习 RAG 时可以把这个文件看成“知识库问答的检索段”：
它不生成最终回答，只负责从规则知识库里找证据，并判断证据是否足够可靠。
"""

from __future__ import annotations

from typing import Any

from aptguide2.rag.confidence import check_confidence
from aptguide2.rag.schemas import KBSource, QueryUnderstandingResult
from aptguide2.tools.vector_adapter import VectorAdapter


def retrieve_kb(
    query_result: QueryUnderstandingResult,
    vector_adapter: VectorAdapter,
    embed_fn,
    top_k: int = 10,
) -> tuple[list[KBSource], bool]:
    """Retrieve KB sources with multi-recall and confidence gate.

    Channels:
    - original query
    - normalized query (soft preferences joined)
    - step-back query for lease/payment/policy questions
    - optional HyDE only for recall when top score is below threshold

    Args:
        query_result: Parsed query understanding result.
        vector_adapter: Vector adapter for Milvus search.
        embed_fn: Async function to embed text -> list[float].
        top_k: Number of results per recall channel.

    Returns:
        Tuple of (sources, is_confident).
        If not confident, sources may still be returned for fallback display.
    """
    # 1. 构造多路召回 query。
    # 同一个用户问题会从多个角度去查向量库，减少单一表达导致的漏召回。
    queries = _build_recall_queries(query_result)

    # 2. 多路向量召回。
    # 每一路 query 都会 embedding 后搜索 KB collection；chunk_id 用来跨路去重。
    all_results: list[dict] = []
    seen_chunk_ids: set[str] = set()

    for query_text, recall_source in queries:
        # embed_fn 在测试里可以是同步假函数；生产里通常接 embedding 服务。
        vector = embed_fn(query_text)
        results = vector_adapter.search_kb(
            vector=vector,
            filters={"module": None, "risk_level": None},
            top_k=top_k,
        )
        for r in results:
            cid = r.get("chunk_id", "")
            if cid and cid not in seen_chunk_ids:
                seen_chunk_ids.add(cid)
                r["_recall_source"] = recall_source
                r["_matched_query"] = query_text
                all_results.append(r)

    # 3. 合并同一 chunk 的多次命中，保留最高相似度和对应的召回来源。
    merged = _merge_by_chunk_id(all_results)

    # 4. 轻量来源重排：在向量相似度基础上加业务规则分。
    reranked = _source_rerank(merged, query_result)

    # 5. 转成稳定 schema，避免后续回答层依赖 Milvus 原始返回结构。
    sources = []
    for r in reranked:
        sources.append(KBSource(
            chunk_id=r.get("chunk_id", ""),
            doc_id=r.get("doc_id", ""),
            title=r.get("title", ""),
            module=r.get("module", ""),
            content=r.get("content", ""),
            score=r.get("_best_score", 0.0),
            risk_level=r.get("risk_level", "low"),
            matched_query=r.get("_matched_query", ""),
            recall_source=r.get("_recall_source", "original"),
        ))

    # 6. 置信度闸门：尤其是押金、违约、合同等高风险问题，证据不够就不答。
    is_confident = check_confidence(sources, query_result.risk_level)

    return sources, is_confident


def _build_recall_queries(query_result: QueryUnderstandingResult) -> list[tuple[str, str]]:
    """Build (query_text, recall_source) pairs for multi-channel recall."""
    queries: list[tuple[str, str]] = []

    # 原始 query 保留用户表达，适合召回标题或内容中直接包含同义表达的 chunk。
    queries.append((query_result.raw_message, "original"))

    # 归一化 query 使用 query understanding 得到的偏好词，适合处理口语化输入。
    if query_result.soft_preferences:
        normalized = " ".join(query_result.soft_preferences)
        if normalized != query_result.raw_message:
            queries.append((normalized, "normalized"))

    # step-back query 把具体问题上提到规则层面。
    # 例如“押金多久到账”不只查“多久到账”，还查“押金退还规则/流程”。
    if query_result.task == "kb_qa" and query_result.risk_level in ("medium", "high"):
        step_back = _build_step_back_query(query_result.raw_message)
        if step_back:
            queries.append((step_back, "step_back"))

    return queries


def _build_step_back_query(message: str) -> str | None:
    """Generate a step-back query for policy questions.

    E.g., "押金退还多久到账" -> "租房押金退还规则 流程 时间"
    """
    step_back_map = {
        "押金": "租房押金退还规则 流程",
        "退租": "退租流程 提前退租 规则",
        "违约": "租赁违约 违约金 规则",
        "续租": "续租续约 流程 规则",
        "预约": "看房预约 规则 流程",
        "取消": "取消预约 规则",
        "报修": "报修维修 流程",
        "投诉": "投诉处理 流程",
        "宠物": "宠物政策 规定",
        "隐私": "隐私保护 账号安全",
        "注销": "账号注销 流程",
    }
    for keyword, step_back in step_back_map.items():
        if keyword in message:
            return step_back
    return None


def _merge_by_chunk_id(results: list[dict]) -> list[dict]:
    """Merge results by chunk_id, keeping best score."""
    merged: dict[str, dict] = {}
    for r in results:
        cid = r.get("chunk_id", "")
        if not cid:
            continue
        score = r.get("distance", 0.0)
        if cid in merged:
            # 一个 chunk 可能被 original 和 step_back 同时召回；最高分代表它最强的一次匹配。
            if score > merged[cid].get("_best_score", 0):
                merged[cid]["_best_score"] = score
                merged[cid]["_matched_query"] = r.get("_matched_query", "")
                merged[cid]["_recall_source"] = r.get("_recall_source", "")
        else:
            r["_best_score"] = score
            merged[cid] = r
    return list(merged.values())


def _source_rerank(results: list[dict], query_result: QueryUnderstandingResult) -> list[dict]:
    """Rerank sources by relevance.

    Boost: module match, risk_level match, keyword overlap, score threshold.
    """
    query = query_result.raw_message

    def sort_key(r: dict) -> float:
        score = r.get("_best_score", 0.0)

        # 字面重合是向量相似度的补充信号。
        # MVP 阶段用字符集合近似，后续可以换成 BM25 或 cross-encoder reranker。
        title = r.get("title", "")
        content = r.get("content", "")
        combined = title + content
        # Count matching characters between query and title (simple overlap)
        query_chars = set(query)
        title_chars = set(title)
        overlap = len(query_chars & title_chars)
        if overlap >= 3:
            score += 0.08
        elif overlap >= 2:
            score += 0.04

        # Boost for module match
        module = r.get("module", "")
        if query_result.task == "kb_qa":
            if module in ("lease", "payment") and query_result.risk_level == "high":
                score += 0.05
            if module == "policy" and "政策" in query:
                score += 0.03
            # Module-specific keyword boosts
            module_keywords = {
                "lease": ["合同", "租约", "签约", "退租", "押金", "续租", "违约", "转租"],
                "payment": ["支付", "租金", "水电", "退款", "发票", "逾期"],
                "appointment": ["预约", "看房", "取消", "改期", "迟到"],
                "life": ["报修", "维修", "噪音", "宠物", "电器", "卫生", "快递"],
                "account": ["注册", "密码", "实名", "隐私", "注销", "账号"],
                "policy": ["优惠", "投诉", "换锁", "安全", "同住", "节假日"],
                "search": ["筛选", "排序", "搜索", "照片", "已租"],
            }
            if module in module_keywords:
                for kw in module_keywords[module]:
                    if kw in query:
                        score += 0.06
                        break

        # Slight penalty for very low risk when asking high-risk questions
        if query_result.risk_level == "high" and r.get("risk_level") == "low":
            score -= 0.02
        return score

    return sorted(results, key=sort_key, reverse=True)
