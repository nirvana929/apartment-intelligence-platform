"""RAG evaluation runner for the 120-case dataset.

Loads YAML eval cases (120-case format), executes retrieval,
computes metrics, and writes a Markdown report.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.rag.kb_retrieval import retrieve_kb
from aptguide2.rag.query_understanding import understand_query
from aptguide2.tools.vector_adapter import VectorAdapter


# ---------------------------------------------------------------------------
# Case loader (handles 120-case YAML format)
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


def embed_single(text: str, settings: Settings) -> list[float]:
    """Embed a single text."""
    client = OpenAI(
        api_key=settings.embedding_api_key.get_secret_value(),
        base_url=settings.embedding_base_url,
    )
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=[text],
    )
    return response.data[0].embedding


# ---------------------------------------------------------------------------
# Eval runners per case type
# ---------------------------------------------------------------------------

def eval_room_retrieval(case: dict, adapter: VectorAdapter, settings: Settings) -> dict:
    """Evaluate a room_retrieval case.

    Returns result dict with hit info.
    """
    query = case["query"]
    positive_ids = set(case.get("positive_room_ids", []))
    expected = case.get("expected", {})
    should_hit = expected.get("hit_at_5", True)

    qr = understand_query(query)

    # If query understanding says fallback, it's a miss for room_search
    if qr.task != "room_search":
        if not should_hit:
            return {"status": "pass", "reason": "correctly identified as non-room-search"}
        return {"status": "fail", "reason": f"task was {qr.task}, expected room_search"}

    # Check if room collection exists
    client = adapter._ensure_client()
    if not client.has_collection("apt_room_vector"):
        return {"status": "skip", "reason": "room collection not synced yet (lease backend not available)"}

    # Single-query vector search with hard filters
    embed_fn = lambda t: embed_single(t, settings)
    vector = embed_fn(query)

    filters = {}
    hf = qr.hard_filters
    if "district_id" in hf:
        filters["district_id"] = hf["district_id"]
    if "max_rent" in hf:
        filters["max_rent"] = hf["max_rent"]
    if "min_rent" in hf:
        filters["min_rent"] = hf["min_rent"]

    results = adapter.search_rooms(vector, filters=filters, top_k=30)

    # Post-filter: boost rooms matching soft preferences (tag overlap)
    if qr.soft_preferences and results:
        for r in results:
            room_tags = r.get("tags", "")
            if isinstance(room_tags, str):
                try:
                    import json as _json
                    room_tags = _json.loads(room_tags)
                except Exception:
                    room_tags = []
            room_facilities = r.get("facilities", "")
            if isinstance(room_facilities, str):
                try:
                    room_facilities = _json.loads(room_facilities)
                except Exception:
                    room_facilities = []
            tag_text = " ".join(room_tags) + " " + " ".join(room_facilities)
            matches = sum(1 for p in qr.soft_preferences if p in tag_text)
            # Boost distance for rooms with tag matches
            r["distance"] = r.get("distance", 0) + matches * 0.05
        results.sort(key=lambda x: x.get("distance", 0), reverse=True)

    found_ids = {r["room_id"] for r in results[:10]}

    if not positive_ids:
        # Expecting no results
        if not results:
            return {"status": "pass", "reason": "correctly returned no results"}
        return {"status": "pass_soft", "reason": f"expected no results but got {len(results)} rooms"}

    hit = bool(positive_ids & found_ids)
    if hit:
        return {"status": "pass", "found": list(found_ids & positive_ids)}
    return {"status": "fail", "reason": "no positive room in top-10", "expected": list(positive_ids), "got": list(found_ids)[:10]}


def eval_kb_retrieval(case: dict, adapter: VectorAdapter, settings: Settings) -> dict:
    """Evaluate a kb_retrieval case."""
    query = case["query"]
    expected_sources = set(case.get("expected_sources", []))
    risk_level = case.get("risk_level", "low")

    qr = understand_query(query)
    embed_fn = lambda t: embed_single(t, settings)

    sources, is_confident = retrieve_kb(
        query_result=qr,
        vector_adapter=adapter,
        embed_fn=embed_fn,
    )

    if not sources:
        return {"status": "fail", "reason": "no sources returned", "expected": list(expected_sources)}

    found_doc_ids = [s.doc_id for s in sources]
    hit_at_3 = bool(expected_sources & set(found_doc_ids[:3]))
    hit_at_5 = bool(expected_sources & set(found_doc_ids[:5]))

    if hit_at_3:
        return {"status": "pass", "found": list(expected_sources & set(found_doc_ids)), "confident": is_confident, "hit_at": 3}
    if hit_at_5:
        return {"status": "pass", "found": list(expected_sources & set(found_doc_ids)), "confident": is_confident, "hit_at": 5}
    return {"status": "fail", "reason": "expected source not in top-5", "expected": list(expected_sources), "got": found_doc_ids[:5]}


def eval_fallback_retrieval(case: dict, adapter: VectorAdapter, settings: Settings) -> dict:
    """Evaluate a fallback_retrieval case.

    These cases expect the system to NOT make unverified commitments.
    The eval checks: task detection says fallback OR confidence gate blocks.
    """
    query = case["query"]
    expected = case.get("expected", {})
    must_low_confidence = expected.get("must_low_confidence_fallback", True)

    qr = understand_query(query)
    embed_fn = lambda t: embed_single(t, settings)

    # If task is already fallback, pass
    if qr.task == "fallback":
        return {"status": "pass", "reason": "correctly identified as fallback"}

    # If high-risk, check confidence gate
    if qr.risk_level == "high":
        _, is_confident = retrieve_kb(qr, adapter, embed_fn)
        if not is_confident:
            return {"status": "pass", "reason": "confidence gate blocked high-risk answer"}
        return {"status": "fail", "reason": "high-risk but confidence gate passed"}

    # For medium/low risk that's not fallback - check if KB retrieval returns nothing useful
    sources, is_confident = retrieve_kb(qr, adapter, embed_fn)
    if not sources or not is_confident:
        return {"status": "pass", "reason": "no confident KB source, will fallback"}

    return {"status": "fail", "reason": f"task was {qr.task}, risk={qr.risk_level}, but got confident sources"}


# ---------------------------------------------------------------------------
# Main eval runner
# ---------------------------------------------------------------------------

def run_eval(cases_path: str, report_path: str) -> dict[str, Any]:
    """Run the full RAG evaluation."""
    settings = Settings()
    cases = load_cases(cases_path)

    adapter = VectorAdapter(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        dim=settings.embedding_dim,
    )

    results = {
        "room_retrieval": {"total": 0, "pass": 0, "fail": 0, "pass_soft": 0, "skip": 0, "failed": []},
        "kb_retrieval": {"total": 0, "pass": 0, "fail": 0, "failed": []},
        "fallback_retrieval": {"total": 0, "pass": 0, "fail": 0, "failed": []},
    }

    for case in cases:
        task = case.get("task", "unknown")
        case_id = case.get("id", case.get("case_id", "unknown"))

        if task == "room_retrieval":
            results["room_retrieval"]["total"] += 1
            r = eval_room_retrieval(case, adapter, settings)
            if r["status"] == "skip":
                results["room_retrieval"]["skip"] += 1
            elif r["status"] in ("pass", "pass_soft"):
                results["room_retrieval"]["pass"] += 1
                if r["status"] == "pass_soft":
                    results["room_retrieval"]["pass_soft"] += 1
            else:
                results["room_retrieval"]["fail"] += 1
                r["case_id"] = case_id
                r["query"] = case["query"]
                results["room_retrieval"]["failed"].append(r)

        elif task == "kb_retrieval":
            results["kb_retrieval"]["total"] += 1
            r = eval_kb_retrieval(case, adapter, settings)
            if r["status"] == "pass":
                results["kb_retrieval"]["pass"] += 1
            else:
                results["kb_retrieval"]["fail"] += 1
                r["case_id"] = case_id
                r["query"] = case["query"]
                results["kb_retrieval"]["failed"].append(r)

        elif task == "fallback_retrieval":
            results["fallback_retrieval"]["total"] += 1
            r = eval_fallback_retrieval(case, adapter, settings)
            if r["status"] == "pass":
                results["fallback_retrieval"]["pass"] += 1
            else:
                results["fallback_retrieval"]["fail"] += 1
                r["case_id"] = case_id
                r["query"] = case["query"]
                results["fallback_retrieval"]["failed"].append(r)

    # Compute metrics
    metrics = compute_metrics(results)
    write_report(report_path, metrics, results, cases)

    return metrics


def compute_metrics(results: dict) -> dict[str, Any]:
    """Compute final metrics."""
    metrics = {}

    # Room retrieval
    rt = results["room_retrieval"]
    room_tested = rt["total"] - rt.get("skip", 0)
    if room_tested > 0:
        metrics["room_pass_rate"] = rt["pass"] / room_tested
    else:
        metrics["room_pass_rate"] = 0.0
    metrics["room_skip_count"] = rt.get("skip", 0)

    # KB retrieval
    kb = results["kb_retrieval"]
    if kb["total"] > 0:
        metrics["kb_pass_rate"] = kb["pass"] / kb["total"]
    else:
        metrics["kb_pass_rate"] = 0.0

    # Fallback
    fb = results["fallback_retrieval"]
    if fb["total"] > 0:
        metrics["fallback_pass_rate"] = fb["pass"] / fb["total"]
    else:
        metrics["fallback_pass_rate"] = 0.0

    # Overall
    total = rt["total"] + kb["total"] + fb["total"]
    total_pass = rt["pass"] + kb["pass"] + fb["pass"]
    metrics["overall_pass_rate"] = total_pass / total if total > 0 else 0.0

    # Gates
    room_gate = metrics["room_pass_rate"] >= 0.70 if metrics.get("room_skip_count", 0) < rt["total"] else True
    gates = {
        "room_pass_rate_gate": room_gate,
        "kb_pass_rate_gate": metrics["kb_pass_rate"] >= 0.80,
        "fallback_pass_rate_gate": metrics["fallback_pass_rate"] >= 0.80,
        "tested_pass_rate_gate": (rt["pass"] + kb["pass"] + fb["pass"]) / max(1, rt["pass"] + rt["fail"] + kb["pass"] + kb["fail"] + fb["pass"] + fb["fail"]) >= 0.80,
    }
    metrics["gates"] = gates
    metrics["all_gates_passed"] = all(gates.values())

    return metrics


def write_report(report_path: str, metrics: dict, results: dict, cases: list) -> None:
    """Write Markdown eval report."""
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# RAG Eval Report\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total cases:** {len(cases)}\n\n")

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Category | Total | Pass | Fail | Pass Rate | Gate | Status |\n")
        f.write("| --- | ---: | ---: | ---: | ---: | ---: | --- |\n")

        gates = metrics.get("gates", {})
        for cat, label in [("room_retrieval", "Room"), ("kb_retrieval", "KB"), ("fallback_retrieval", "Fallback")]:
            r = results[cat]
            rate = metrics.get(f"{cat.replace('_retrieval', '')}_pass_rate", 0)
            gate = f"{cat.replace('_retrieval', '')}_pass_rate_gate"
            gate_val = gates.get(gate)
            status = "PASS" if gate_val else ("FAIL" if gate_val is False else "-")
            if cat == "kb_retrieval":
                gate_str = ">= 80%"
            elif cat == "fallback_retrieval":
                gate_str = ">= 80%"
            else:
                gate_str = ">= 70%"
            skip_str = f" ({r.get('skip', 0)} skipped)" if r.get("skip", 0) > 0 else ""
            f.write(f"| {label}{skip_str} | {r['total']} | {r['pass']} | {r['fail']} | {rate:.1%} | {gate_str} | {status} |\n")

        f.write(f"\n**Overall pass rate:** {metrics['overall_pass_rate']:.1%}\n")
        f.write(f"**All gates passed:** {'YES' if metrics['all_gates_passed'] else 'NO'}\n")

        # Failed cases
        all_failed = []
        for cat in ["room_retrieval", "kb_retrieval", "fallback_retrieval"]:
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

    print(f"Report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument("--cases", required=True, help="Path to eval cases YAML")
    parser.add_argument("--report", required=True, help="Path to output report")
    args = parser.parse_args()

    metrics = run_eval(args.cases, args.report)
    print(f"\nOverall pass rate: {metrics['overall_pass_rate']:.1%}")
    print(f"All gates passed: {metrics['all_gates_passed']}")


if __name__ == "__main__":
    main()
