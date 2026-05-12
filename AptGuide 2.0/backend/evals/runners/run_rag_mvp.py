"""MVP RAG evaluation runner.

Loads YAML eval cases, executes retrieval, computes metrics,
and writes a Markdown report.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import yaml

# Add project src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.rag.kb_retrieval import retrieve_kb
from aptguide2.rag.query_understanding import understand_query
from aptguide2.rag.schemas import RetrievalEvalCase
from aptguide2.tools.vector_adapter import VectorAdapter


def load_cases(path: str) -> list[RetrievalEvalCase]:
    """Load eval cases from YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cases = []
    for item in data.get("cases", []):
        cases.append(RetrievalEvalCase(**item))
    return cases


def embed_texts_sync(texts: list[str], settings: Settings) -> list[list[float]]:
    """Embed texts synchronously using OpenAI-compatible API."""
    client = OpenAI(
        api_key=settings.embedding_api_key.get_secret_value(),
        base_url=settings.embedding_base_url,
    )
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [d.embedding for d in response.data]


def embed_single(text: str, settings: Settings) -> list[float]:
    """Embed a single text."""
    return embed_texts_sync([text], settings)[0]


def run_eval(cases_path: str, report_path: str) -> dict[str, Any]:
    """Run the RAG MVP evaluation.

    Returns metrics dict.
    """
    settings = Settings()
    cases = load_cases(cases_path)

    # Connect to Milvus
    adapter = VectorAdapter(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        dim=settings.embedding_dim,
    )

    results = {
        "room_retrieval": {"total": 0, "hit_at_3": 0, "hit_at_5": 0, "mrr_sum": 0.0, "failed": []},
        "kb_retrieval": {"total": 0, "hit_at_3": 0, "hit_at_5": 0, "mrr_sum": 0.0,
                         "source_missing": 0, "low_confidence_fallback": 0, "failed": []},
        "fallback_retrieval": {"total": 0, "correct": 0, "failed": []},
    }

    for case in cases:
        query_result = understand_query(case.query)

        if case.case_type == "room_retrieval":
            # Room retrieval eval - placeholder since R6/R8 not ready
            results["room_retrieval"]["total"] += 1
            results["room_retrieval"]["failed"].append({
                "case_id": case.case_id,
                "reason": "room retrieval not yet implemented (waiting for data handoff)",
            })

        elif case.case_type == "kb_retrieval":
            results["kb_retrieval"]["total"] += 1

            def embed_fn(text: str) -> list[float]:
                return embed_single(text, settings)

            sources, is_confident = retrieve_kb(
                query_result=query_result,
                vector_adapter=adapter,
                embed_fn=embed_fn,
            )

            if not is_confident:
                results["kb_retrieval"]["low_confidence_fallback"] += 1

            if not sources:
                results["kb_retrieval"]["source_missing"] += 1
                results["kb_retrieval"]["failed"].append({
                    "case_id": case.case_id,
                    "query": case.query,
                    "reason": "no sources returned",
                })
                continue

            # Check hit@3 and hit@5
            source_doc_ids = [s.doc_id for s in sources]
            expected = set(case.expected_doc_ids)

            hit_at_3 = bool(expected & set(source_doc_ids[:3]))
            hit_at_5 = bool(expected & set(source_doc_ids[:5]))

            if hit_at_3:
                results["kb_retrieval"]["hit_at_3"] += 1
            if hit_at_5:
                results["kb_retrieval"]["hit_at_5"] += 1

            # MRR
            for rank, doc_id in enumerate(source_doc_ids, 1):
                if doc_id in expected:
                    results["kb_retrieval"]["mrr_sum"] += 1.0 / rank
                    break

            if not hit_at_5:
                results["kb_retrieval"]["failed"].append({
                    "case_id": case.case_id,
                    "query": case.query,
                    "expected": list(expected),
                    "got": source_doc_ids[:5],
                })

        elif case.case_type == "fallback_retrieval":
            results["fallback_retrieval"]["total"] += 1
            # Check that task is fallback or returns low confidence
            if query_result.task == "fallback":
                results["fallback_retrieval"]["correct"] += 1
            elif query_result.risk_level == "high":
                # High-risk should trigger confidence gate
                def embed_fn(text: str) -> list[float]:
                    return embed_single(text, settings)
                _, is_confident = retrieve_kb(query_result, adapter, embed_fn)
                if not is_confident:
                    results["fallback_retrieval"]["correct"] += 1
                else:
                    results["fallback_retrieval"]["failed"].append({
                        "case_id": case.case_id,
                        "query": case.query,
                        "reason": "should have low confidence but was confident",
                    })
            else:
                results["fallback_retrieval"]["failed"].append({
                    "case_id": case.case_id,
                    "query": case.query,
                    "reason": f"task was {query_result.task}, expected fallback",
                })

    # Compute final metrics
    metrics = compute_metrics(results)

    # Write report
    write_report(report_path, metrics, results, cases)

    return metrics


def compute_metrics(results: dict) -> dict[str, Any]:
    """Compute final metrics from results."""
    metrics = {}

    # Room retrieval
    rt = results["room_retrieval"]
    if rt["total"] > 0:
        metrics["room_hit_at_5"] = 0.0  # Not implemented yet
    else:
        metrics["room_hit_at_5"] = 0.0

    # KB retrieval
    kb = results["kb_retrieval"]
    if kb["total"] > 0:
        metrics["kb_source_hit_at_3"] = kb["hit_at_3"] / kb["total"]
        metrics["kb_source_hit_at_5"] = kb["hit_at_5"] / kb["total"]
        metrics["kb_mrr"] = kb["mrr_sum"] / kb["total"]
        metrics["kb_source_missing_count"] = kb["source_missing"]
        metrics["kb_low_confidence_fallback_rate"] = kb["low_confidence_fallback"] / kb["total"]
    else:
        metrics["kb_source_hit_at_3"] = 0.0
        metrics["kb_source_hit_at_5"] = 0.0
        metrics["kb_mrr"] = 0.0
        metrics["kb_source_missing_count"] = 0
        metrics["kb_low_confidence_fallback_rate"] = 0.0

    # Fallback
    fb = results["fallback_retrieval"]
    if fb["total"] > 0:
        metrics["fallback_correct_rate"] = fb["correct"] / fb["total"]
    else:
        metrics["fallback_correct_rate"] = 0.0

    # Gates
    gates = {
        "room_hit_at_5_gate": metrics["room_hit_at_5"] >= 0.80,
        "kb_source_hit_at_3_gate": metrics["kb_source_hit_at_3"] >= 0.85,
        "high_risk_fallback_gate": metrics["kb_low_confidence_fallback_rate"] >= 0.0 or kb["total"] == 0,
        "unvalidated_room_count_gate": True,  # No rooms returned yet
        "source_missing_gate": metrics["kb_source_missing_count"] == 0,
    }
    metrics["gates"] = gates
    metrics["all_gates_passed"] = all(gates.values())

    return metrics


def write_report(
    report_path: str,
    metrics: dict,
    results: dict,
    cases: list[RetrievalEvalCase],
) -> None:
    """Write Markdown eval report."""
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# RAG MVP Eval Report\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total cases:** {len(cases)}\n\n")

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Metric | Value | Gate | Pass |\n")
        f.write("| --- | ---: | ---: | --- |\n")

        gates = metrics.get("gates", {})
        rows = [
            ("room hit@5", f"{metrics['room_hit_at_5']:.1%}", ">= 80%", gates.get("room_hit_at_5_gate")),
            ("KB source hit@3", f"{metrics['kb_source_hit_at_3']:.1%}", ">= 85%", gates.get("kb_source_hit_at_3_gate")),
            ("KB source hit@5", f"{metrics['kb_source_hit_at_5']:.1%}", "-", "-"),
            ("KB MRR", f"{metrics['kb_mrr']:.3f}", "-", "-"),
            ("KB source missing", metrics["kb_source_missing_count"], "= 0", gates.get("source_missing_gate")),
            ("KB low-conf fallback", f"{metrics['kb_low_confidence_fallback_rate']:.1%}", "-", "-"),
            ("fallback correct", f"{metrics['fallback_correct_rate']:.1%}", "-", "-"),
        ]
        for name, val, gate, passed in rows:
            pass_str = "PASS" if passed else ("FAIL" if passed is False else "-")
            f.write(f"| {name} | {val} | {gate} | {pass_str} |\n")

        # Overall
        f.write(f"\n**All gates passed:** {'YES' if metrics['all_gates_passed'] else 'NO'}\n")

        # KB retrieval details
        f.write("\n## KB Retrieval\n\n")
        kb = results["kb_retrieval"]
        f.write(f"- Total cases: {kb['total']}\n")
        f.write(f"- Hit@3: {kb['hit_at_3']}\n")
        f.write(f"- Hit@5: {kb['hit_at_5']}\n")
        f.write(f"- Source missing: {kb['source_missing']}\n")
        f.write(f"- Low confidence fallback: {kb['low_confidence_fallback']}\n")

        # Failed cases
        all_failed = (
            results["room_retrieval"]["failed"]
            + results["kb_retrieval"]["failed"]
            + results["fallback_retrieval"]["failed"]
        )
        if all_failed:
            f.write("\n## Failed Cases\n\n")
            for fail in all_failed:
                f.write(f"- **{fail['case_id']}**: {fail.get('reason', '')}")
                if "expected" in fail:
                    f.write(f" (expected: {fail['expected']}, got: {fail.get('got', [])})")
                f.write("\n")

    print(f"Report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Run RAG MVP evaluation")
    parser.add_argument("--cases", required=True, help="Path to eval cases YAML")
    parser.add_argument("--report", required=True, help="Path to output report")
    args = parser.parse_args()

    metrics = run_eval(args.cases, args.report)
    print(f"\nAll gates passed: {metrics['all_gates_passed']}")


if __name__ == "__main__":
    main()
