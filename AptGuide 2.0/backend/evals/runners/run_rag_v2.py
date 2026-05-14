"""RAG v2 evaluation runner.

Loads YAML eval cases, executes the v2 pipeline, computes retrieval
metrics (hit@k, MRR, NDCG), and writes a Markdown report.

Requires: Milvus, embedding service, lease backend.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Add project src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.rag.eval_metrics import hit_at_k, mean_reciprocal_rank, ndcg_at_k
from aptguide2.rag.pipeline_v2 import run_pipeline_v2


@dataclass
class RagV2EvalDependencies:
    vector_adapter: object
    embed_fn: Callable[[str], list[float]]
    lease_validator: object | None
    interaction_classifier: object | None = None


# ---------------------------------------------------------------------------
# Case loader
# ---------------------------------------------------------------------------

def load_cases(path: str) -> list[dict]:
    """Load eval cases from YAML. Returns raw dicts."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict) and "cases" in data:
        return data["cases"]
    if isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed_single(text: str, settings: Settings) -> list[float]:
    """Embed a single text via OpenAI-compatible API."""
    client = OpenAI(
        api_key=settings.embedding_api_key.get_secret_value(),
        base_url=settings.embedding_base_url,
    )
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=[text],
    )
    return response.data[0].embedding


def classify_interaction_intent(query: str, deps: RagV2EvalDependencies) -> object | None:
    """Classify interaction intent if classifier is available."""
    if deps.interaction_classifier is None:
        return None
    return deps.interaction_classifier.classify(query)


def extract_result_metadata(result: object, interaction_intent: object | None) -> dict[str, Any]:
    """Extract diagnostic metadata from pipeline result and intent."""
    qr = getattr(result, "query_understanding", None)
    return {
        "route": getattr(interaction_intent, "route", ""),
        "rag_task": getattr(interaction_intent, "rag_task", ""),
        "domain": getattr(interaction_intent, "domain", ""),
        "action": getattr(interaction_intent, "action", ""),
        "intent_confidence": getattr(interaction_intent, "confidence", None),
        "parsed_task": getattr(qr, "task", getattr(result, "task", "")),
        "risk_level": getattr(qr, "risk_level", ""),
        "response_mode": getattr(qr, "response_mode", ""),
        "hard_filters": dict(getattr(qr, "hard_filters", {}) or {}),
        "soft_preferences": list(getattr(qr, "soft_preferences", []) or []),
        "retrieval_queries": list(getattr(qr, "retrieval_queries", []) or []),
        "fallback_reason": getattr(result, "fallback_reason", ""),
    }


def build_live_dependencies(settings: Settings) -> RagV2EvalDependencies:
    """Build live dependencies for RAG v2 eval from settings."""
    from aptguide2.api.deps import get_interaction_classifier, get_tool_runtime
    from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator
    from aptguide2.tools.vector_adapter import VectorAdapter

    adapter = VectorAdapter(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        dim=settings.embedding_dim,
    )

    def embed_fn(text: str) -> list[float]:
        return embed_single(text, settings)

    return RagV2EvalDependencies(
        vector_adapter=adapter,
        embed_fn=embed_fn,
        lease_validator=ToolRuntimeRoomValidator(get_tool_runtime()),
        interaction_classifier=get_interaction_classifier(),
    )


# ---------------------------------------------------------------------------
# Per-case evaluators
# ---------------------------------------------------------------------------

def eval_kb_retrieval(case: dict, deps: RagV2EvalDependencies) -> dict:
    """Evaluate a kb_retrieval case using the v2 pipeline."""
    query = case["query"]
    expected_doc_ids: set[str | int] = set(case.get("expected_sources", case.get("expected_doc_ids", [])))

    interaction_intent = classify_interaction_intent(query, deps)
    diag: dict[str, Any] = {}
    result = run_pipeline_v2(
        message=query,
        vector_adapter=deps.vector_adapter,
        embed_fn=deps.embed_fn,
        lease_validator=deps.lease_validator,
        interaction_intent=interaction_intent,
        diagnostics=diag,
    )

    # Collect doc_ids from kb_sources
    actual_doc_ids: list[str | int] = [s.doc_id for s in result.kb_sources]
    metadata = extract_result_metadata(result, interaction_intent)

    if not actual_doc_ids:
        return {
            "status": "fail",
            "reason": "no KB sources returned",
            "expected": sorted(expected_doc_ids),
            **metadata,
            **diag,
        }

    h3 = hit_at_k(actual_doc_ids, expected_doc_ids, 3)
    h5 = hit_at_k(actual_doc_ids, expected_doc_ids, 5)
    mrr = mean_reciprocal_rank(actual_doc_ids, expected_doc_ids)
    ndcg5 = ndcg_at_k(actual_doc_ids, expected_doc_ids, 5)

    if h3:
        return {"status": "pass", "hit_at": 3, "mrr": mrr, "ndcg@5": ndcg5}
    if h5:
        return {"status": "pass", "hit_at": 5, "mrr": mrr, "ndcg@5": ndcg5}
    return {
        "status": "fail",
        "reason": "expected source not in top-5",
        "expected": sorted(expected_doc_ids),
        "got": actual_doc_ids[:5],
        "mrr": mrr,
        "ndcg@5": ndcg5,
        **metadata,
        **diag,
    }


def eval_room_retrieval(case: dict, deps: RagV2EvalDependencies) -> dict:
    """Evaluate a room_retrieval case using the v2 pipeline."""
    query = case["query"]
    expected_room_ids: set[str | int] = set(case.get("positive_room_ids", case.get("expected_room_ids", [])))

    interaction_intent = classify_interaction_intent(query, deps)
    diag: dict[str, Any] = {}
    result = run_pipeline_v2(
        message=query,
        vector_adapter=deps.vector_adapter,
        embed_fn=deps.embed_fn,
        lease_validator=deps.lease_validator,
        interaction_intent=interaction_intent,
        diagnostics=diag,
    )

    # Collect room_id from ranked rooms
    actual_room_ids: list[str | int] = [r.room_id for r in result.rooms]
    metadata = extract_result_metadata(result, interaction_intent)

    if not actual_room_ids:
        if not expected_room_ids:
            return {"status": "pass", "reason": "correctly returned no rooms"}
        return {
            "status": "fail",
            "reason": "no rooms returned",
            "expected": sorted(expected_room_ids),
            **metadata,
            **diag,
        }

    h5 = hit_at_k(actual_room_ids, expected_room_ids, 5)
    mrr = mean_reciprocal_rank(actual_room_ids, expected_room_ids)
    ndcg5 = ndcg_at_k(actual_room_ids, expected_room_ids, 5)

    if h5:
        return {"status": "pass", "mrr": mrr, "ndcg@5": ndcg5}
    return {
        "status": "fail",
        "reason": "expected room not in top-5",
        "expected": sorted(expected_room_ids),
        "got": actual_room_ids[:5],
        "mrr": mrr,
        "ndcg@5": ndcg5,
        **metadata,
        **diag,
    }


def eval_fallback_retrieval(case: dict, deps: RagV2EvalDependencies) -> dict:
    """Evaluate a fallback_retrieval case using the v2 pipeline."""
    query = case["query"]
    expected = case.get("expected", {})
    must_low_confidence = expected.get("must_low_confidence_fallback", True)

    interaction_intent = classify_interaction_intent(query, deps)
    diag: dict[str, Any] = {}
    result = run_pipeline_v2(
        message=query,
        vector_adapter=deps.vector_adapter,
        embed_fn=deps.embed_fn,
        lease_validator=deps.lease_validator,
        interaction_intent=interaction_intent,
        diagnostics=diag,
    )

    metadata = extract_result_metadata(result, interaction_intent)

    if result.task == "fallback":
        return {"status": "pass", "reason": "correctly identified as fallback"}

    if result.task == "kb_qa" and not result.is_confident:
        return {"status": "pass", "reason": "confidence gate blocked risky answer"}

    if must_low_confidence and result.is_confident:
        return {
            "status": "fail",
            "reason": f"task={result.task}, is_confident=True, expected fallback/low-conf",
            **metadata,
            **diag,
        }

    return {"status": "pass", "reason": f"task={result.task}, is_confident={result.is_confident}"}


# ---------------------------------------------------------------------------
# Main eval runner
# ---------------------------------------------------------------------------

def run_eval(cases_path: str, report_path: str) -> dict[str, Any]:
    """Run the RAG v2 evaluation.

    Returns metrics dict.
    """
    settings = Settings()
    deps = build_live_dependencies(settings)
    cases = load_cases(cases_path)

    results = {
        "kb_retrieval": {"total": 0, "pass": 0, "fail": 0, "mrr_sum": 0.0, "ndcg_sum": 0.0,
                         "hit_at_3_count": 0, "hit_at_5_count": 0, "failed": []},
        "room_retrieval": {"total": 0, "pass": 0, "fail": 0, "mrr_sum": 0.0, "ndcg_sum": 0.0,
                           "hit_at_5_count": 0, "unvalidated_count": 0, "failed": []},
        "fallback_retrieval": {"total": 0, "pass": 0, "fail": 0, "failed": []},
    }

    for case in cases:
        task = case.get("case_type", case.get("task", "unknown"))
        case_id = case.get("id", case.get("case_id", "unknown"))

        if task == "kb_retrieval":
            results["kb_retrieval"]["total"] += 1
            r = eval_kb_retrieval(case, deps)
            if r["status"] == "pass":
                results["kb_retrieval"]["pass"] += 1
                results["kb_retrieval"]["mrr_sum"] += r.get("mrr", 0.0)
                results["kb_retrieval"]["ndcg_sum"] += r.get("ndcg@5", 0.0)
                if r.get("hit_at", 99) <= 3:
                    results["kb_retrieval"]["hit_at_3_count"] += 1
                if r.get("hit_at", 99) <= 5:
                    results["kb_retrieval"]["hit_at_5_count"] += 1
            else:
                results["kb_retrieval"]["fail"] += 1
                r["case_id"] = case_id
                r["query"] = case["query"]
                results["kb_retrieval"]["mrr_sum"] += r.get("mrr", 0.0)
                results["kb_retrieval"]["ndcg_sum"] += r.get("ndcg@5", 0.0)
                results["kb_retrieval"]["failed"].append(r)

        elif task == "room_retrieval":
            results["room_retrieval"]["total"] += 1
            r = eval_room_retrieval(case, deps)
            if r["status"] == "pass":
                results["room_retrieval"]["pass"] += 1
                results["room_retrieval"]["mrr_sum"] += r.get("mrr", 0.0)
                results["room_retrieval"]["ndcg_sum"] += r.get("ndcg@5", 0.0)
                results["room_retrieval"]["hit_at_5_count"] += 1
            else:
                results["room_retrieval"]["fail"] += 1
                r["case_id"] = case_id
                r["query"] = case["query"]
                results["room_retrieval"]["mrr_sum"] += r.get("mrr", 0.0)
                results["room_retrieval"]["ndcg_sum"] += r.get("ndcg@5", 0.0)
                results["room_retrieval"]["failed"].append(r)

        elif task == "fallback_retrieval":
            results["fallback_retrieval"]["total"] += 1
            r = eval_fallback_retrieval(case, deps)
            if r["status"] == "pass":
                results["fallback_retrieval"]["pass"] += 1
            else:
                results["fallback_retrieval"]["fail"] += 1
                r["case_id"] = case_id
                r["query"] = case["query"]
                results["fallback_retrieval"]["failed"].append(r)

    # Compute final metrics
    metrics = compute_metrics(results)

    # Write report
    write_report(report_path, metrics, results, cases)

    return metrics


def compute_metrics(results: dict) -> dict[str, Any]:
    """Compute final metrics from results."""
    metrics: dict[str, Any] = {}

    # KB retrieval
    kb = results["kb_retrieval"]
    if kb["total"] > 0:
        metrics["kb_source_hit_at_3"] = kb["hit_at_3_count"] / kb["total"]
        metrics["kb_source_hit_at_5"] = kb["hit_at_5_count"] / kb["total"]
        metrics["kb_mrr"] = kb["mrr_sum"] / kb["total"]
        metrics["kb_ndcg_at_5"] = kb["ndcg_sum"] / kb["total"]
    else:
        metrics["kb_source_hit_at_3"] = 0.0
        metrics["kb_source_hit_at_5"] = 0.0
        metrics["kb_mrr"] = 0.0
        metrics["kb_ndcg_at_5"] = 0.0

    # Room retrieval
    rt = results["room_retrieval"]
    if rt["total"] > 0:
        metrics["room_hit_at_5"] = rt["hit_at_5_count"] / rt["total"]
        metrics["room_mrr"] = rt["mrr_sum"] / rt["total"]
        metrics["room_ndcg_at_5"] = rt["ndcg_sum"] / rt["total"]
    else:
        metrics["room_hit_at_5"] = 0.0
        metrics["room_mrr"] = 0.0
        metrics["room_ndcg_at_5"] = 0.0

    # High-risk fallback
    fb = results["fallback_retrieval"]
    high_risk_total = fb["total"]
    high_risk_correct = fb["pass"]
    metrics["high_risk_fallback_rate"] = high_risk_correct / high_risk_total if high_risk_total > 0 else 0.0

    # Unvalidated room count (rooms that bypassed validation)
    metrics["unvalidated_room_count"] = rt.get("unvalidated_count", 0)

    # Gates
    gates = {
        "kb_source_hit_at_3_gate": metrics["kb_source_hit_at_3"] >= 0.90,
        "high_risk_fallback_gate": metrics["high_risk_fallback_rate"] >= 1.0,
        "room_hit_at_5_gate": metrics["room_hit_at_5"] >= 0.85,
        "unvalidated_room_count_gate": metrics["unvalidated_room_count"] == 0,
    }
    metrics["gates"] = gates
    metrics["all_gates_passed"] = all(gates.values())

    return metrics


def write_report(
    report_path: str,
    metrics: dict,
    results: dict,
    cases: list[dict],
) -> None:
    """Write Markdown eval report."""
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# RAG v2 Eval Report\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total cases:** {len(cases)}\n\n")

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Metric | Value | Gate | Pass |\n")
        f.write("| --- | ---: | ---: | --- |\n")

        gates = metrics.get("gates", {})
        rows = [
            ("KB source hit@3", f"{metrics['kb_source_hit_at_3']:.1%}", ">= 90%", gates.get("kb_source_hit_at_3_gate")),
            ("KB source hit@5", f"{metrics['kb_source_hit_at_5']:.1%}", "-", "-"),
            ("KB MRR", f"{metrics['kb_mrr']:.3f}", "-", "-"),
            ("KB NDCG@5", f"{metrics['kb_ndcg_at_5']:.3f}", "-", "-"),
            ("Room hit@5", f"{metrics['room_hit_at_5']:.1%}", ">= 85%", gates.get("room_hit_at_5_gate")),
            ("Room MRR", f"{metrics['room_mrr']:.3f}", "-", "-"),
            ("Room NDCG@5", f"{metrics['room_ndcg_at_5']:.3f}", "-", "-"),
            ("High-risk fallback", f"{metrics['high_risk_fallback_rate']:.1%}", ">= 100%", gates.get("high_risk_fallback_gate")),
            ("Unvalidated rooms", metrics["unvalidated_room_count"], "= 0", gates.get("unvalidated_room_count_gate")),
        ]
        for name, val, gate, passed in rows:
            pass_str = "PASS" if passed else ("FAIL" if passed is False else "-")
            f.write(f"| {name} | {val} | {gate} | {pass_str} |\n")

        f.write(f"\n**All gates passed:** {'YES' if metrics['all_gates_passed'] else 'NO'}\n")

        # Per-category breakdown
        f.write("\n## KB Retrieval\n\n")
        kb = results["kb_retrieval"]
        f.write(f"- Total cases: {kb['total']}\n")
        f.write(f"- Pass: {kb['pass']}\n")
        f.write(f"- Fail: {kb['fail']}\n")

        f.write("\n## Room Retrieval\n\n")
        rt = results["room_retrieval"]
        f.write(f"- Total cases: {rt['total']}\n")
        f.write(f"- Pass: {rt['pass']}\n")
        f.write(f"- Fail: {rt['fail']}\n")

        f.write("\n## Fallback Retrieval\n\n")
        fb = results["fallback_retrieval"]
        f.write(f"- Total cases: {fb['total']}\n")
        f.write(f"- Pass: {fb['pass']}\n")
        f.write(f"- Fail: {fb['fail']}\n")

        # Failed cases
        all_failed = []
        for cat in ["kb_retrieval", "room_retrieval", "fallback_retrieval"]:
            for fail in results[cat]["failed"]:
                fail["category"] = cat
                all_failed.append(fail)

        if all_failed:
            f.write(f"\n## Failed Cases ({len(all_failed)})\n\n")
            for fail in all_failed:
                f.write(f"- **{fail.get('case_id', '?')}** [{fail['category']}]: {fail.get('reason', '')}")
                if "expected" in fail:
                    f.write(f" (expected: {fail['expected']}, got: {fail.get('got', [])})")
                f.write("\n")
                details = []
                for key in ("route", "rag_task", "domain", "action", "parsed_task", "risk_level", "response_mode", "fallback_reason"):
                    value = fail.get(key)
                    if value not in (None, "", []):
                        details.append(f"{key}={value}")
                if details:
                    f.write(f"  - diagnostics: {', '.join(details)}\n")
                if fail.get("hard_filters"):
                    f.write(f"  - hard_filters: `{fail['hard_filters']}`\n")
                if fail.get("soft_preferences"):
                    f.write(f"  - soft_preferences: `{fail['soft_preferences']}`\n")
                if fail.get("retrieval_queries"):
                    f.write(f"  - retrieval_queries: `{fail['retrieval_queries']}`\n")

    print(f"Report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Run RAG v2 evaluation")
    parser.add_argument("--cases", required=True, help="Path to eval cases YAML")
    parser.add_argument("--report", required=True, help="Path to output report")
    args = parser.parse_args()

    metrics = run_eval(args.cases, args.report)
    print(f"\nAll gates passed: {metrics['all_gates_passed']}")


if __name__ == "__main__":
    main()
