from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("aptguide2")


def emit_event(event: str, **fields: Any) -> dict[str, Any]:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload
