"""Inspect room identity source fields without mutating data.

Reports:
  - Milvus wechat_room_index fields
  - sample source_record_id values
  - whether lease_room_id / room_id / house_id / apartment_id exists
  - candidate MySQL/wechat table fields if configured
  - lease validation accepted ID shape

Usage:
    cd backend && uv run python scripts/inspect_room_identity_sources.py
"""

from __future__ import annotations

import os
import sys

# Ensure the backend src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from pymilvus import MilvusClient
except ImportError:
    MilvusClient = None  # type: ignore[assignment,misc]


WECHAT_ROOM_COLLECTION = "wechat_room_index"
MILVUS_URI = os.environ.get("MILVUS_URI", "http://localhost:19530")


def _print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _print_field(field: dict) -> None:
    name = field.get("name", "?")
    dtype = field.get("type", "?")
    is_primary = field.get("is_primary", False)
    desc = field.get("description", "")
    primary_tag = " [PRIMARY KEY]" if is_primary else ""
    print(f"  - {name} (type={dtype}{primary_tag}){': ' + desc if desc else ''}")


def main() -> None:
    if MilvusClient is None:
        print("ERROR: pymilvus is not installed. Install it with: pip install pymilvus")
        sys.exit(1)

    client = MilvusClient(uri=MILVUS_URI)

    # --- 1. Milvus wechat_room_index fields ---
    _print_header("Milvus wechat_room_index Fields")
    try:
        schema = client.describe_collection(WECHAT_ROOM_COLLECTION)
        fields = schema.get("fields", [])
        if not fields:
            print("  (no fields found or collection does not exist)")
        else:
            for f in fields:
                _print_field(f)
    except Exception as exc:
        print(f"  ERROR describing collection: {exc}")

    # --- 2. Sample source_record_id values ---
    _print_header("Sample Source Record IDs (first 10 rows)")
    try:
        client.load_collection(WECHAT_ROOM_COLLECTION)
        sample = client.query(
            collection_name=WECHAT_ROOM_COLLECTION,
            filter="",
            output_fields=["id"],
            limit=10,
        )
        if not sample:
            print("  (no rows returned)")
        else:
            for row in sample:
                rid = row.get("id", "")
                print(f"  source_record_id = {rid!r}")
    except Exception as exc:
        print(f"  ERROR querying samples: {exc}")

    # --- 3. Check for identity-relevant fields ---
    _print_header("Identity Field Presence Check")
    try:
        schema = client.describe_collection(WECHAT_ROOM_COLLECTION)
        field_names = {f.get("name", "") for f in schema.get("fields", [])}
        identity_fields = [
            "lease_room_id",
            "room_id",
            "house_id",
            "apartment_id",
        ]
        for fname in identity_fields:
            present = fname in field_names
            status = "PRESENT" if present else "MISSING"
            print(f"  {fname}: {status}")
    except Exception as exc:
        print(f"  ERROR checking fields: {exc}")

    # --- 4. Candidate MySQL/wechat table fields ---
    _print_header("Candidate MySQL / WeChat Table Fields")
    mysql_host = os.environ.get("MYSQL_HOST", "")
    if mysql_host:
        print(f"  MYSQL_HOST configured: {mysql_host}")
        print("  (MySQL inspection requires a live connection; skipping in this script)")
    else:
        print("  MYSQL_HOST not configured; skipping MySQL inspection")

    # --- 5. Lease validation accepted ID shape ---
    _print_header("Lease Validation Accepted ID Shape")
    print("  The lease API expects lease_room_id as a numeric string or integer.")
    print("  Example: lease_room_id = '101' or lease_room_id = 101")
    print("  If Milvus wechat_room_index stores wechat IDs (e.g., 'wx-abc-123'),")
    print("  those are NOT valid lease_room_id values -- an identity mapping step is required.")

    _print_header("Summary")
    print("  - wechat_room_index uses 'id' as the Milvus primary key (source_record_id).")
    print("  - If lease_room_id is MISSING from the schema, the identity mapping must")
    print("    be populated from an external source (e.g., MySQL room_identity_map table).")
    print("  - Synthetic hash IDs (900000+) are generated at query time and must never")
    print("    be passed to the lease validation API.")
    print()


if __name__ == "__main__":
    main()
