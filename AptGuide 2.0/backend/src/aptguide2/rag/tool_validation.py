"""RAG v2 validation adapters over governed ToolRuntime."""

from __future__ import annotations

from uuid import uuid4

from aptguide2.harness.tools.contracts import ToolCallRequest


class ToolRuntimeRoomValidator:
    def __init__(self, tool_runtime):
        self.tool_runtime = tool_runtime

    def search_rooms(self, payload: dict) -> dict:
        result = self.tool_runtime.execute(
            ToolCallRequest(
                tool="room.search",
                request_id=f"r-{uuid4().hex[:8]}",
                payload=payload,
            )
        )
        if not result.ok:
            return {"rooms": []}
        return result.data if isinstance(result.data, dict) else {"rooms": []}
