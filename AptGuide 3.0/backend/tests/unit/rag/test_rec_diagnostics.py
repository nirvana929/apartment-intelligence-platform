from aptguide3.rag.diagnostics import KbRecDiagnostic, RoomRecDiagnostic


def test_room_rec_diagnostic_report_contains_stage_counts():
    diagnostic = RoomRecDiagnostic(
        raw_message="找番禺1500以内安静一点的房子",
        semantic_queries=["番禺 1500以内 安静 房子"],
        vector_hits_total=10,
        vector_unique_room_count=4,
        lease_validation_requested_count=4,
        lease_validated_count=2,
        lease_dropped_room_ids=[3, 4],
        final_room_ids=[1, 2],
    )

    report = diagnostic.to_report_dict()

    assert report["vector_hits_total"] == 10
    assert report["lease_dropped_room_ids"] == [3, 4]
    assert report["final_room_ids"] == [1, 2]


def test_kb_rec_diagnostic_report_contains_source_counts():
    diagnostic = KbRecDiagnostic(
        raw_message="押金不退怎么办",
        semantic_queries=["押金不退 处理"],
        vector_hits_total=8,
        unique_chunk_count=5,
        returned_doc_ids=["KB-LEASE-005"],
        returned_chunk_ids=["chunk-1"],
        confidence_passed=True,
    )

    report = diagnostic.to_report_dict()

    assert report["vector_hits_total"] == 8
    assert report["returned_doc_ids"] == ["KB-LEASE-005"]
    assert report["confidence_passed"] is True
