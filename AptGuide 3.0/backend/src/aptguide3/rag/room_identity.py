from __future__ import annotations

from pydantic import BaseModel


class RoomIdentity(BaseModel):
    """Maps a source room record to its business identity in the lease system."""

    source_system: str
    source_record_id: str
    canonical_room_id: str = ""
    business_system: str = "lease"
    business_room_id: str | None = None
    verification_status: str = "unmapped"
    match_method: str = "unmapped"
    match_confidence: float = 0.0


def is_lease_verifiable(identity: RoomIdentity) -> bool:
    """Return True only when the identity has a verified lease business room ID."""
    return (
        identity.business_system == "lease"
        and bool(identity.business_room_id)
        and identity.verification_status == "verified"
    )


def evidence_level_for_identity(identity: RoomIdentity) -> str:
    """Classify the evidence level for a room identity.

    Returns:
        "mapped_verified" -- has verified lease business room ID
        "mapped_candidate" -- has a candidate mapping but not yet verified
        "vector_only" -- only exists as a vector recall hit, no business identity
    """
    if is_lease_verifiable(identity):
        return "mapped_verified"
    if identity.verification_status == "candidate":
        return "mapped_candidate"
    return "vector_only"
