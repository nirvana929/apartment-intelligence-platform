from __future__ import annotations

from typing import Any

from aptguide2.harness.tools.contracts import KBSearchInput, ToolCallRequest, ToolCallResult


class KBSearchExecutor:
    """Execute KB search through vector adapter."""

    def __init__(self, vector_adapter: Any, embed_fn: Any) -> None:
        self.vector_adapter = vector_adapter
        self.embed_fn = embed_fn

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        try:
            validated = KBSearchInput(**request.payload)
        except Exception as exc:
            return ToolCallResult.error_result(
                tool=request.tool,
                code="INVALID_PAYLOAD",
                message=str(exc),
                backend="vector",
            )

        try:
            vector = self.embed_fn(validated.query)
        except Exception as exc:
            return ToolCallResult.error_result(
                tool=request.tool,
                code="UNKNOWN_TOOL_ERROR",
                message=f"Embed failed: {exc}",
                backend="vector",
            )

        try:
            raw_results = self.vector_adapter.search_kb(
                vector,
                filters=validated.filters,
                top_k=validated.top_k,
            )
        except Exception as exc:
            return ToolCallResult.error_result(
                tool=request.tool,
                code="UNKNOWN_TOOL_ERROR",
                message=f"Vector search failed: {exc}",
                backend="vector",
            )

        sources = []
        for item in raw_results:
            sources.append({
                "chunk_id": item.get("chunk_id", ""),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "module": item.get("module", ""),
                "score": item.get("distance", 0.0),
            })

        return ToolCallResult.ok_result(
            tool=request.tool,
            data={"sources": sources, "total": len(sources)},
            backend="vector",
        )
