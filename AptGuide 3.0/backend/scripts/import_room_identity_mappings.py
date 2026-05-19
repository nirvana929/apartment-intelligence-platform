"""Import room identity mappings from CSV into RoomIdentityRepository.

CSV columns (required):
  source_system, source_record_id, canonical_room_id, business_system,
  business_room_id, verification_status, match_method, match_confidence

Usage:
  uv run python scripts/import_room_identity_mappings.py --csv evals/datasets/room_identity_mappings.csv
"""
from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from aptguide3.config import get_settings
from aptguide3.rag.room_identity import RoomIdentity


def parse_csv(path: Path) -> list[RoomIdentity]:
    required = {
        "source_system", "source_record_id", "canonical_room_id",
        "business_system", "business_room_id", "verification_status",
        "match_method", "match_confidence",
    }
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"CSV missing required columns: {missing}")
        identities = []
        for row in reader:
            identities.append(RoomIdentity(
                source_system=row["source_system"],
                source_record_id=row["source_record_id"],
                canonical_room_id=row.get("canonical_room_id", ""),
                business_system=row.get("business_system", "lease"),
                business_room_id=row.get("business_room_id") or None,
                verification_status=row.get("verification_status", "unmapped"),
                match_method=row.get("match_method", "unmapped"),
                match_confidence=float(row.get("match_confidence", 0)),
            ))
    return identities


async def import_mappings(csv_path: Path) -> int:
    settings = get_settings()
    mode = settings.persistence_mode

    if mode in ("mysql", "hybrid"):
        from aptguide3.database.database import build_sessionmaker
        from aptguide3.persistence.mysql_repos import MySqlRoomIdentityRepository
        sm = build_sessionmaker(settings.mysql_dsn)
        repo = MySqlRoomIdentityRepository(sm)
    else:
        from aptguide3.persistence.room_identity_repo import InMemoryRoomIdentityRepository
        repo = InMemoryRoomIdentityRepository()

    identities = parse_csv(csv_path)
    for identity in identities:
        await repo.upsert_mapping(identity)
    return len(identities)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import room identity mappings from CSV")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    args = parser.parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    count = asyncio.run(import_mappings(csv_path))
    print(f"imported {count} room identity mappings")


if __name__ == "__main__":
    main()
