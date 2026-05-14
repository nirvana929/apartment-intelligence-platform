from __future__ import annotations

import time
from typing import Any, Protocol

from aptguide2.harness.tools.contracts import ToolCallRequest, ToolCallResult, ToolDefinition
from aptguide2.harness.tools.errors import ToolExecutionError, ToolNotFoundError, ToolTimeoutError
from aptguide2.harness.tools.registry import ToolRegistry
from aptguide2.harness.tools.trace import summarize_tool_request, summarize_tool_result


class ToolExecutor(Protocol):
    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        ...


class ToolRuntime:
    """Governed tool execution with permission checks and error normalization."""

    def __init__(self, registry: ToolRegistry, recorder: Any = None) -> None:
        self.registry = registry
        self._executors: dict[str, ToolExecutor] = {}
        self._recorder = recorder

    def register_executor(self, tool_name: str, executor: ToolExecutor) -> None:
        self._executors[tool_name] = executor

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        definition = self._get_definition(request.tool)

        trace_token = None
        if self._recorder is not None:
            trace_token = self._recorder.start_stage(
                f"tool.{request.tool}",
                definition.backend,
                summarize_tool_request(request, definition),
            )

        if definition.requires_user and not request.user_id:
            result = ToolCallResult.error_result(
                tool=request.tool,
                code="MISSING_USER_ID",
                message=f"Tool {request.tool} requires user_id",
                backend=definition.backend,
            )
            if trace_token is not None:
                self._recorder.finish_stage(trace_token, summarize_tool_result(result), errors=[result.error.message])
            return result

        if definition.requires_confirmation and not request.confirmation_id:
            result = ToolCallResult.error_result(
                tool=request.tool,
                code="CONFIRMATION_REQUIRED",
                message=f"Tool {request.tool} requires confirmation",
                backend=definition.backend,
            )
            if trace_token is not None:
                self._recorder.finish_stage(trace_token, summarize_tool_result(result), errors=[result.error.message])
            return result

        executor = self._executors.get(request.tool)
        if executor is None:
            result = ToolCallResult.error_result(
                tool=request.tool,
                code="TOOL_NOT_IMPLEMENTED",
                message=f"No executor registered for {request.tool}",
                backend=definition.backend,
            )
            if trace_token is not None:
                self._recorder.finish_stage(trace_token, summarize_tool_result(result), errors=[result.error.message])
            return result

        start = time.perf_counter()
        try:
            result = executor.execute(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.metadata.setdefault("backend", definition.backend)
            result.metadata.setdefault("latency_ms", round(elapsed_ms, 3))
            if request.trace_id:
                result.metadata["trace_id"] = request.trace_id
            if trace_token is not None:
                self._recorder.finish_stage(trace_token, summarize_tool_result(result))
            return result
        except (ToolTimeoutError, TimeoutError) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            result = ToolCallResult.error_result(
                tool=request.tool,
                code="TOOL_TIMEOUT",
                message=str(exc) or "tool timed out",
                recoverable=True,
                backend=definition.backend,
            )
            if trace_token is not None:
                self._recorder.finish_stage(trace_token, summarize_tool_result(result), errors=[result.error.message])
            return result
        except ToolExecutionError as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            result = ToolCallResult.error_result(
                tool=request.tool,
                code="UNKNOWN_TOOL_ERROR",
                message=str(exc),
                backend=definition.backend,
            )
            if trace_token is not None:
                self._recorder.finish_stage(trace_token, summarize_tool_result(result), errors=[result.error.message])
            return result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            result = ToolCallResult.error_result(
                tool=request.tool,
                code="UNKNOWN_TOOL_ERROR",
                message=f"{type(exc).__name__}: {exc}",
                backend=definition.backend,
            )
            if trace_token is not None:
                self._recorder.finish_stage(trace_token, summarize_tool_result(result), errors=[result.error.message])
            return result

    def _get_definition(self, name: str) -> ToolDefinition:
        try:
            return self.registry.get(name)
        except ToolNotFoundError:
            raise ToolNotFoundError(f"Tool not found: {name}")
