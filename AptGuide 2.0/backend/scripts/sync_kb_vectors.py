"""KB vector sync script.

Loads reviewed YAML rules, builds chunks, embeds changed chunks,
upserts to Milvus, and marks deleted chunks inactive.

学习入口：这条脚本是“知识库文档 -> chunk -> embedding -> Milvus”的离线入库链路。
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import yaml

# Add project src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.rag.chunking import build_kb_chunks, compute_content_hash
from aptguide2.rag.schemas import KBChunk
from aptguide2.tools.vector_adapter import VectorAdapter


def load_rules(rules_dir: str) -> list[dict]:
    """Load all YAML rule files from directory, deduplicating by doc_id."""
    rules = []
    seen_ids: set[str] = set()
    pattern = os.path.join(rules_dir, "*.yaml")
    for filepath in sorted(glob.glob(pattern)):
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            for item in items:
                doc_id = item.get("doc_id", "")
                if doc_id and doc_id in seen_ids:
                    continue
                if doc_id:
                    seen_ids.add(doc_id)
                rules.append(item)
    return rules


def validate_rules(rules: list[dict]) -> tuple[list[dict], list[str]]:
    """Validate rules and return (valid_rules, errors)."""
    valid = []
    errors = []
    seen_ids = set()

    for rule in rules:
        doc_id = rule.get("doc_id")
        if not doc_id:
            errors.append(f"Missing doc_id in rule: {rule.get('title', 'unknown')}")
            continue
        if doc_id in seen_ids:
            errors.append(f"Duplicate doc_id: {doc_id}")
            continue
        seen_ids.add(doc_id)

        # 只允许经过审核的规则入库。RAG 不是知识生产者，入库前质量控制很重要。
        status = rule.get("status", "")
        if status not in ("reviewed", "approved", "active"):
            errors.append(f"{doc_id}: status '{status}' is not reviewed/approved/active")
            continue

        # Check reviewed_by
        if not rule.get("reviewed_by"):
            errors.append(f"{doc_id}: missing reviewed_by")
            continue

        # 入库前做 PII 检查，避免向量库保存手机号、身份证、银行卡等敏感信息。
        content = rule.get("content", "")
        if _contains_pii(content):
            errors.append(f"{doc_id}: content contains PII (phone/ID/bank card)")
            continue

        # 高风险模块必须显式标注 risk_level，后续 confidence gate 会依赖它。
        high_risk_modules = {"lease", "payment", "account"}
        if rule.get("module") in high_risk_modules and not rule.get("risk_level"):
            errors.append(f"{doc_id}: high-risk module '{rule['module']}' missing risk_level")
            continue

        valid.append(rule)

    return valid, errors


def _contains_pii(text: str) -> bool:
    """Check if text contains phone, ID card, or bank card patterns."""
    import re
    # Phone numbers (Chinese mobile)
    if re.search(r"1[3-9]\d{9}", text):
        return True
    # ID card (18 digits or 15 digits)
    if re.search(r"\d{17}[\dXx]", text):
        return True
    # Bank card (16-19 digits)
    if re.search(r"\d{16,19}", text):
        return True
    return False


def embed_texts(texts: list[str], settings: Settings) -> list[list[float]]:
    """Embed a list of texts using OpenAI-compatible API."""
    if not texts:
        return []

    client = OpenAI(
        api_key=settings.embedding_api_key.get_secret_value(),
        base_url=settings.embedding_base_url,
    )

    # 分批 embedding，避免超过供应商批量限制。
    all_embeddings = []
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        all_embeddings.extend([d.embedding for d in response.data])

    return all_embeddings


def run_sync(release_id: str, rules_dir: str | None = None) -> dict:
    """Run the KB vector sync process.

    Returns sync report dict.
    """
    settings = Settings()
    rules_path = rules_dir or settings.kb_rules_dir

    report = {
        "sync_id": f"kb-sync-{int(time.time())}",
        "release_id": release_id,
        "added": 0,
        "updated": 0,
        "inactive": 0,
        "embedded": 0,
        "failed": 0,
        "errors": [],
    }

    # 1. 从 YAML 加载并校验业务规则。
    rules = load_rules(rules_path)
    valid_rules, validation_errors = validate_rules(rules)
    report["errors"].extend(validation_errors)

    if not valid_rules:
        report["errors"].append("No valid rules found")
        return report

    # 2. 把规则拆成 KB chunk；每个 chunk 是向量库里的一个检索单元。
    all_chunks: list[KBChunk] = []
    for rule in valid_rules:
        chunks = build_kb_chunks(rule, release_id)
        # Set status to "indexed" after embedding into Milvus
        for chunk in chunks:
            chunk.status = "indexed"
        all_chunks.extend(chunks)

    if not all_chunks:
        report["errors"].append("No chunks generated")
        return report

    # 3. 确保 Milvus collection 存在。
    adapter = VectorAdapter(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        dim=settings.embedding_dim,
    )
    adapter.ensure_kb_collection()

    # 4. 查已有 content_hash，只对变化的 chunk 重新 embedding。
    chunk_ids = [c.chunk_id for c in all_chunks]
    existing = adapter.get_kb_chunks_by_ids(chunk_ids)
    existing_hashes = {r["chunk_id"]: r.get("content_hash", "") for r in existing}

    # 5. 增量同步：新增或内容变化才进入 changed_chunks。
    changed_chunks = []
    for chunk in all_chunks:
        old_hash = existing_hashes.get(chunk.chunk_id)
        if old_hash != chunk.content_hash:
            changed_chunks.append(chunk)

    if not changed_chunks:
        report["errors"].append("No changes detected")
        return report

    # 6. 对变化 chunk 生成向量。这里再次拼接元信息作为 embedding 输入。
    kb_prefix = "[lease][rule]"
    texts = []
    for chunk in changed_chunks:
        tag_str = ",".join(chunk.tags)
        text = f"[{chunk.module}][{chunk.doc_type}][{chunk.title}][{tag_str}][{chunk.risk_level}]\n{chunk.content}"
        texts.append(text)

    embeddings = embed_texts(texts, settings)

    # 7. 写入 Milvus；同主键 chunk_id 会覆盖旧版本。
    upsert_pairs = list(zip(changed_chunks, embeddings))
    upserted = adapter.upsert_kb_chunks(upsert_pairs)

    # Count added vs updated
    for chunk in changed_chunks:
        if chunk.chunk_id in existing_hashes:
            report["updated"] += 1
        else:
            report["added"] += 1

    report["embedded"] = upserted

    # 8. 当前 YAML 不再包含的 chunk 标记 inactive，而不是物理删除，方便追踪。
    all_current_ids = set(chunk_ids)
    # Query all active chunks in Milvus
    client = adapter._ensure_client()
    all_active = client.query(
        collection_name="apt_rental_kb",
        filter='status in ["active", "indexed"]',
        output_fields=["chunk_id"],
    )
    stale_ids = [r["chunk_id"] for r in all_active if r["chunk_id"] not in all_current_ids]
    if stale_ids:
        adapter.mark_kb_inactive(stale_ids)
        report["inactive"] = len(stale_ids)

    return report


def main():
    parser = argparse.ArgumentParser(description="Sync KB vectors to Milvus")
    parser.add_argument("--release-id", required=True, help="KB release ID")
    parser.add_argument("--rules-dir", default=None, help="Path to rules YAML directory")
    args = parser.parse_args()

    report = run_sync(args.release_id, args.rules_dir)

    # Write report
    report_dir = Path(__file__).resolve().parent.parent.parent / "evals" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "vector_sync_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# KB Vector Sync Report\n\n")
        f.write(f"**Sync ID:** {report['sync_id']}\n")
        f.write(f"**Release ID:** {report['release_id']}\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"| --- | ---: |\n")
        f.write(f"| Added | {report['added']} |\n")
        f.write(f"| Updated | {report['updated']} |\n")
        f.write(f"| Inactive | {report['inactive']} |\n")
        f.write(f"| Embedded | {report['embedded']} |\n")
        f.write(f"| Failed | {report['failed']} |\n")
        if report["errors"]:
            f.write(f"\n## Errors\n\n")
            for err in report["errors"]:
                f.write(f"- {err}\n")

    print(f"Sync complete. Report: {report_path}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
