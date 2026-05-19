"""Sync KB vectors from reviewed rules to Milvus.

Usage:
    uv run python scripts/sync_kb_vectors.py

Requires: APTGUIDE3_VECTOR_URI, APTGUIDE3_EMBEDDING_API_KEY, KB rules JSON input
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aptguide3.rag.chunking import build_kb_chunk_text, compute_content_hash, validate_kb_rule


def validate_and_prepare(rules: list[dict]) -> tuple[list[dict], list[dict]]:
    valid = []
    rejected = []
    for rule in rules:
        errors = validate_kb_rule(rule)
        if errors:
            rejected.append({"doc_id": rule.get("doc_id", "?"), "errors": errors})
        else:
            content = build_kb_chunk_text(rule)
            valid.append({
                "chunk_id": f"kb-{rule['doc_id']}",
                "doc_id": rule["doc_id"],
                "title": rule.get("title", ""),
                "module": rule.get("module", ""),
                "content": content,
                "risk_level": rule.get("risk_level", "low"),
                "content_hash": compute_content_hash(content),
                "status": rule.get("status", "active"),
            })
    return valid, rejected


if __name__ == "__main__":
    print("KB sync template ready. Provide rules JSON to validate and prepare.")
