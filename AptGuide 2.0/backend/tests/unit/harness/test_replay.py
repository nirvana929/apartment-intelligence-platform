import json

import pytest

from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
from aptguide2.harness.errors import ReplayPIIError
from aptguide2.harness.replay import ReplayWriter


def test_replay_writer_writes_jsonl(tmp_path):
    path = tmp_path / "replay.jsonl"
    writer = ReplayWriter(path)
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    resp = AptGuideResponse(
        request_id="r-1",
        trace_id="t-1",
        reply="ok",
        phase="idle",
        domain_category="in_domain",
    )
    writer.write(req, resp)
    rows = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    payload = json.loads(rows[0])
    assert payload["request"]["request_id"] == "r-1"


def test_replay_writer_rejects_pii_key(tmp_path):
    writer = ReplayWriter(tmp_path / "replay.jsonl")
    req = AptGuideRequest(
        request_id="r-1",
        message="找房",
        client_context={"phone": "123"},
    )
    resp = AptGuideResponse(
        request_id="r-1",
        trace_id="t-1",
        reply="ok",
        phase="idle",
        domain_category="in_domain",
    )
    with pytest.raises(ReplayPIIError):
        writer.write(req, resp)
