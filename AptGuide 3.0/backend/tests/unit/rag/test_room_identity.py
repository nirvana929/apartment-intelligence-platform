from aptguide3.rag.room_identity import RoomIdentity, evidence_level_for_identity, is_lease_verifiable


def test_verified_identity_is_lease_verifiable():
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-1",
        canonical_room_id="room-canon-1",
        business_room_id="101",
        verification_status="verified",
        match_method="direct_id",
        match_confidence=1.0,
    )
    assert is_lease_verifiable(identity) is True


def test_unmapped_identity_is_vector_only():
    identity = RoomIdentity(source_system="wechat", source_record_id="wx-1")
    assert evidence_level_for_identity(identity) == "vector_only"


def test_candidate_identity_is_mapped_candidate():
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-2",
        verification_status="candidate",
        match_method="field_similarity",
        match_confidence=0.75,
    )
    assert evidence_level_for_identity(identity) == "mapped_candidate"


def test_verified_without_business_room_id_is_not_lease_verifiable():
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-3",
        verification_status="verified",
        business_room_id=None,
    )
    assert is_lease_verifiable(identity) is False
    assert evidence_level_for_identity(identity) == "vector_only"


def test_verified_with_non_lease_business_system_is_not_lease_verifiable():
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-4",
        business_system="internal",
        business_room_id="999",
        verification_status="verified",
    )
    assert is_lease_verifiable(identity) is False


def test_default_room_identity_values():
    identity = RoomIdentity(source_system="wechat", source_record_id="wx-5")
    assert identity.business_system == "lease"
    assert identity.business_room_id is None
    assert identity.verification_status == "unmapped"
    assert identity.match_method == "unmapped"
    assert identity.match_confidence == 0.0
