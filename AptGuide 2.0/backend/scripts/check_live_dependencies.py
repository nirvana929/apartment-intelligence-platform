from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.system.readiness import DependencyCheck, ReadinessReport, render_markdown_report
from aptguide2.tools.lease_adapter import LeaseAdapter
from aptguide2.tools.vector_adapter import KB_COLLECTION, ROOM_COLLECTION, VectorAdapter


def check_milvus(settings: Settings) -> DependencyCheck:
    try:
        adapter = VectorAdapter(
            uri=settings.milvus_uri,
            token=settings.milvus_token,
            dim=settings.embedding_dim,
        )
        client = adapter._ensure_client()
        room_ok = client.has_collection(ROOM_COLLECTION)
        kb_ok = client.has_collection(KB_COLLECTION)
        return DependencyCheck(
            name="milvus",
            ok=room_ok and kb_ok,
            detail=f"{ROOM_COLLECTION}={room_ok}, {KB_COLLECTION}={kb_ok}",
        )
    except Exception as exc:
        return DependencyCheck(name="milvus", ok=False, detail=f"{type(exc).__name__}: {exc}")


def check_embedding(settings: Settings) -> DependencyCheck:
    try:
        client = OpenAI(
            api_key=settings.embedding_api_key.get_secret_value(),
            base_url=settings.embedding_base_url,
        )
        response = client.embeddings.create(model=settings.embedding_model, input=["AptGuide readiness check"])
        dim = len(response.data[0].embedding)
        return DependencyCheck(
            name="embedding",
            ok=dim == settings.embedding_dim,
            detail=f"model={settings.embedding_model}, dim={dim}, expected={settings.embedding_dim}",
        )
    except Exception as exc:
        return DependencyCheck(name="embedding", ok=False, detail=f"{type(exc).__name__}: {exc}")


def check_lease(settings: Settings) -> DependencyCheck:
    async def _run() -> bool:
        adapter = LeaseAdapter(
            base_url=settings.lease_base_url,
            timeout=settings.lease_timeout_seconds,
            internal_token=settings.lease_internal_token,
        )
        try:
            return await adapter.health()
        finally:
            await adapter.close()

    try:
        ok = asyncio.run(_run())
        return DependencyCheck(name="lease", ok=ok, detail=f"base_url={settings.lease_base_url}")
    except Exception as exc:
        return DependencyCheck(name="lease", ok=False, detail=f"{type(exc).__name__}: {exc}")


def build_report(settings: Settings) -> ReadinessReport:
    return ReadinessReport(checks=[
        check_milvus(settings),
        check_embedding(settings),
        check_lease(settings),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Check live AptGuide dependencies")
    parser.add_argument("--report", required=True, help="Markdown report path")
    args = parser.parse_args()

    report = build_report(Settings())
    output_path = Path(args.report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(report), encoding="utf-8")
    print(f"Report written to: {output_path}")
    raise SystemExit(0 if report.all_required_ok else 2)


if __name__ == "__main__":
    main()
