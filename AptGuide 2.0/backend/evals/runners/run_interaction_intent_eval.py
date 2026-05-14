from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from aptguide2.interaction.classifier import HeuristicInteractionClassifier, apply_policy_corrections


def load_cases(path: str) -> list[dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("cases", [])


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, bool]:
    return {
        "route_ok": prediction.get("route") == case.get("expected_route"),
        "rag_task_ok": case.get("expected_rag_task") in (None, prediction.get("rag_task")),
        "domain_ok": case.get("expected_domain") in (None, prediction.get("domain")),
        "action_ok": case.get("expected_action") in (None, prediction.get("action")),
        "risk_ok": case.get("expected_risk_level") in (None, prediction.get("risk_level")),
        "response_mode_ok": case.get("expected_response_mode") in (None, prediction.get("response_mode")),
    }


def run_eval(cases_path: str) -> dict[str, Any]:
    classifier = HeuristicInteractionClassifier()
    cases = load_cases(cases_path)
    scored = []
    for case in cases:
        intent = apply_policy_corrections(classifier.classify(case["query"]))
        scored.append(score_case(case, intent.model_dump(mode="json")))
    total = len(scored)
    exact = sum(1 for item in scored if all(item.values()))
    return {"total": total, "exact": exact, "exact_rate": exact / total if total else 0.0, "scored": scored}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    args = parser.parse_args()
    metrics = run_eval(args.cases)
    print(metrics)


if __name__ == "__main__":
    main()
