from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
from aptguide2.harness.errors import ReplayPIIError

PII_KEYS = {"phone", "id_card", "bank_card", "real_name", "email", "mobile"}


def _assert_no_pii(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in PII_KEYS:
                raise ReplayPIIError(f"PII key is not allowed in replay: {key}")
            _assert_no_pii(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_pii(item)


class ReplayWriter:
    """Writes sanitized replay cases as JSONL."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, request: AptGuideRequest, response: AptGuideResponse) -> None:
        payload = {
            "request": request.model_dump(mode="json"),
            "response": response.model_dump(mode="json"),
        }
        _assert_no_pii(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
