"""Unit tests for import_room_identity_mappings script."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "scripts"))

from import_room_identity_mappings import parse_csv


def test_parse_valid_csv(tmp_path: Path):
    csv_file = tmp_path / "mappings.csv"
    csv_file.write_text(
        "source_system,source_record_id,canonical_room_id,business_system,business_room_id,"
        "verification_status,match_method,match_confidence\n"
        "wechat,WR001,C001,lease,L001,verified,manual,0.95\n"
        "wechat,WR002,C002,lease,,candidate,auto,0.60\n",
        encoding="utf-8",
    )
    identities = parse_csv(csv_file)
    assert len(identities) == 2
    assert identities[0].source_record_id == "WR001"
    assert identities[0].business_room_id == "L001"
    assert identities[1].business_room_id is None


def test_parse_csv_missing_columns(tmp_path: Path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("source_system,source_record_id\nwechat,WR001\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        parse_csv(csv_file)
