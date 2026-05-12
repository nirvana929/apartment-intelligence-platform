from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml


DEFAULT_APTGUIDE_URL = "http://localhost:8100"


@dataclass
class CaseResult:
    suite: str
    case_id: str
    title: str
    model: str
    passed: bool
    classification: str
    expected_path: list[str] = field(default_factory=list)
    actual_path: list[str] = field(default_factory=list)
    failure_node: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    root_cause: str | None = None
    latency_ms: int = 0
    langsmith_project: str | None = None
    langsmith_trace: str | None = None


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def post_chat(
    client: httpx.AsyncClient,
    base_url: str,
    *,
    session_id: str,
    message: str,
    user_id: str = "1",
    body_extra: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    payload: dict[str, Any] = {"session_id": session_id, "message": message}
    if body_extra:
        payload.update(body_extra)
    started = time.perf_counter()
    response = await client.post(
        f"{base_url}/api/chat",
        json=payload,
        headers={"X-User-Id": user_id},
        timeout=60.0,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    response.raise_for_status()
    return response.json(), latency_ms


def write_results(path: Path, results: list[CaseResult], metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": metadata,
        "summary": summarize(results),
        "results": [asdict(r) for r in results],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    by_classification: dict[str, int] = {}
    for r in results:
        by_classification[r.classification] = by_classification.get(r.classification, 0) + 1
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else 0,
        "by_classification": by_classification,
    }


def parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--base-url", default=DEFAULT_APTGUIDE_URL)
    p.add_argument("--model", required=True)
    p.add_argument("--output", default=None)
    p.add_argument("--langsmith-project", default=None)
    return p
