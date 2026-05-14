"""Risk detection eval runner.

Measures:
- risk_accuracy: correct risk_level classification
- response_mode_accuracy: correct response_mode assignment
- high_risk_recall: fraction of high-risk cases correctly identified
- false_block_rate: fraction of non-refuse cases incorrectly refused
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from aptguide2.rag.risk_detection import detect_risk_profile


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f)
    return payload["cases"]


def evaluate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    risk_correct = 0
    mode_correct = 0
    false_blocks = 0
    non_refuse_cases = 0
    high_total = 0
    high_recalled = 0

    for case in cases:
        profile = detect_risk_profile(case["query"])
        expected_risk = case["expected_risk"]
        expected_mode = case["expected_response_mode"]
        should_refuse = bool(case.get("should_refuse", False))

        risk_ok = profile.risk_level == expected_risk
        mode_ok = profile.response_mode == expected_mode
        risk_correct += int(risk_ok)
        mode_correct += int(mode_ok)

        if expected_risk == "high":
            high_total += 1
            high_recalled += int(profile.risk_level == "high")

        if not should_refuse:
            non_refuse_cases += 1
            false_blocks += int(profile.response_mode == "refuse")

        rows.append({
            "id": case["id"],
            "query": case["query"],
            "expected_risk": expected_risk,
            "actual_risk": profile.risk_level,
            "expected_response_mode": expected_mode,
            "actual_response_mode": profile.response_mode,
            "risk_ok": risk_ok,
            "mode_ok": mode_ok,
        })

    total = len(cases)
    return {
        "total": total,
        "risk_accuracy": risk_correct / total if total else 0.0,
        "response_mode_accuracy": mode_correct / total if total else 0.0,
        "high_risk_recall": high_recalled / high_total if high_total else 1.0,
        "false_block_rate": false_blocks / non_refuse_cases if non_refuse_cases else 0.0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default="evals/datasets/risk_detection_cases.yaml",
    )
    args = parser.parse_args()
    report = evaluate_cases(load_cases(Path(args.dataset)))
    print(f"total={report['total']}")
    print(f"risk_accuracy={report['risk_accuracy']:.3f}")
    print(f"response_mode_accuracy={report['response_mode_accuracy']:.3f}")
    print(f"high_risk_recall={report['high_risk_recall']:.3f}")
    print(f"false_block_rate={report['false_block_rate']:.3f}")


if __name__ == "__main__":
    main()
