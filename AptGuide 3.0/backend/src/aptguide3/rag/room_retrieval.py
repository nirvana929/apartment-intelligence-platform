from __future__ import annotations

import asyncio
from typing import Any

from aptguide3.rag.diagnostics import RoomRecDiagnostic
from aptguide3.rag.room_identity import RoomIdentity, evidence_level_for_identity, is_lease_verifiable
from aptguide3.rag.room_ranking import rank_rooms
from aptguide3.rag.schemas import RetrievalPlan, RoomCandidate, ValidatedRoom


def retrieve_ranked_rooms(
    plan: RetrievalPlan,
    vector_client: Any,
    embedding_client: Any,
    lease_client: Any,
    preference_scorer: Any,
    top_n: int = 5,
    top_k: int = 30,
    diagnostic: RoomRecDiagnostic | None = None,
    identity_repo: Any | None = None,
) -> list:
    if plan.task != "room_search":
        return []
    if diagnostic is not None:
        diagnostic.semantic_queries = list(plan.semantic_queries)
        diagnostic.hard_filters = dict(plan.hard_filters)
        diagnostic.soft_preferences = list(plan.soft_preferences)
    best_by_room: dict[int, RoomCandidate] = {}
    strict_hits_seen = 0
    for query in plan.semantic_queries:
        if diagnostic is not None:
            diagnostic.embedding_queries_attempted += 1
        vector = embedding_client.embed(query)
        if not vector:
            if diagnostic is not None:
                diagnostic.embedding_empty_count += 1
            continue
        hits = vector_client.search_wechat_rooms(vector, filters=plan.hard_filters, top_k=top_k)
        strict_hits_seen += len(hits)
        # Fallback: if strict filters return 0 hits, retry with relaxed filters
        # (remove district filter, keep rent filter)
        if not hits and plan.hard_filters.get("district_name"):
            relaxed_filters = {k: v for k, v in plan.hard_filters.items() if k != "district_name"}
            hits = vector_client.search_wechat_rooms(vector, filters=relaxed_filters or None, top_k=top_k)
            if hits and diagnostic is not None:
                diagnostic.resolution_notes = diagnostic.resolution_notes or []
                diagnostic.resolution_notes.append(
                    f"fallback: relaxed district filter for query '{query}', got {len(hits)} hits"
                )
        if diagnostic is not None:
            diagnostic.vector_hits_total += len(hits)
        for hit in hits:
            room_id = int(hit.get("room_id", 0))
            if room_id <= 0:
                continue
            distance = float(hit.get("distance", 1.0))
            semantic_score = max(0.0, min(1.0, 1.0 - distance))
            existing = best_by_room.get(room_id)
            if existing is None or semantic_score > existing.semantic_score:
                best_by_room[room_id] = RoomCandidate(
                    room_id=room_id,
                    apartment_id=hit.get("apartment_id"),
                    semantic_score=semantic_score,
                    matched_query=query,
                    extra={
                        "apartment_name": hit.get("apartment_name", ""),
                        "district_name": hit.get("district_name", ""),
                        "rent": hit.get("rent", 0),
                        "rent_range": hit.get("rent_range", ""),
                        "payment_types": hit.get("payment_types", []),
                        "tags": hit.get("tags", []),
                        "facilities": hit.get("facilities", []),
                        "metro_stations": hit.get("metro_stations", []),
                        # --- source identity fields ---
                        "wechat_room_id": hit.get("wechat_room_id", ""),
                        "lease_room_id": hit.get("lease_room_id"),
                        "source_collection": hit.get("source_collection", ""),
                        "source_record_id": hit.get("source_record_id", ""),
                        "identity_mapping_status": hit.get("identity_mapping_status", "unmapped"),
                    },
                )
    if diagnostic is not None:
        diagnostic.vector_unique_room_count = len(best_by_room)
        diagnostic.vector_top_room_ids = sorted(best_by_room.keys())[:10]
    if not best_by_room:
        if diagnostic is not None:
            diagnostic.failure_stage = "vector_recall_empty"
        return []

    # --- Task 2: Split candidates by lease identity availability ---
    lease_mappable: list[RoomCandidate] = []
    wechat_only: list[RoomCandidate] = []
    wechat_no_lease_id = 0

    for candidate in best_by_room.values():
        extra = candidate.extra or {}
        lease_room_id = extra.get("lease_room_id")
        if not lease_room_id:
            wechat_no_lease_id += 1

        # Attempt identity resolution if repo is available
        identity: RoomIdentity | None = None
        if identity_repo is not None:
            source_system = extra.get("source_system", "wechat")
            source_record_id = extra.get("source_record_id", "")
            if source_record_id:
                identity = _run_async(identity_repo.get_by_source(source_system, source_record_id))

        if identity is not None and is_lease_verifiable(identity):
            # Use the verified business room_id for lease validation
            extra["business_room_id"] = int(identity.business_room_id)
            extra["evidence_level"] = evidence_level_for_identity(identity)
            lease_mappable.append(candidate)
        elif identity is not None:
            extra["evidence_level"] = evidence_level_for_identity(identity)
            wechat_only.append(candidate)
        else:
            extra["evidence_level"] = "vector_only"
            wechat_only.append(candidate)

    if diagnostic is not None:
        diagnostic.wechat_hits_without_lease_id_count = wechat_no_lease_id

    # --- Lease validation for mappable candidates ---
    lease_validated_ids: set[int] = set()
    if lease_mappable:
        business_ids = []
        for c in lease_mappable:
            bid = (c.extra or {}).get("business_room_id")
            if bid:
                business_ids.append(bid)
        if business_ids:
            if diagnostic is not None:
                diagnostic.lease_validation_requested_count = len(business_ids)
            try:
                validated_rooms = _run_async(
                    lease_client.validate_rooms(business_ids, plan.hard_filters)
                )
                for vr in validated_rooms:
                    lease_validated_ids.add(int(vr.get("room_id", 0)))
            except Exception:
                if diagnostic is not None:
                    diagnostic.failure_stage = "lease_validation_error"

    # --- Build ValidatedRoom list ---
    validated = []

    # Lease-validated candidates (highest evidence)
    for candidate in lease_mappable:
        extra = candidate.extra or {}
        business_id = extra.get("business_room_id", 0)
        if business_id in lease_validated_ids:
            validated.append(ValidatedRoom(
                room_id=candidate.room_id,
                apartment_name=extra.get("apartment_name", ""),
                district_name=extra.get("district_name", ""),
                rent=extra.get("rent", 0),
                payment_types=extra.get("payment_types", []),
                tags=extra.get("tags", []),
                facilities=extra.get("facilities", []),
                semantic_score=candidate.semantic_score,
                matched_query=candidate.matched_query,
                wechat_room_id=extra.get("wechat_room_id", ""),
                lease_room_id=business_id,
                source_collection=extra.get("source_collection", ""),
                source_record_id=extra.get("source_record_id", ""),
                lease_validation_status="passed",
                evidence_level="lease_validated",
            ))

    # Wechat-only candidates (demo fallback when no verified identity)
    for candidate in wechat_only:
        extra = candidate.extra or {}
        evidence_level = extra.get("evidence_level", "vector_only")
        validated.append(ValidatedRoom(
            room_id=candidate.room_id,
            apartment_name=extra.get("apartment_name", ""),
            district_name=extra.get("district_name", ""),
            rent=extra.get("rent", 0),
            payment_types=extra.get("payment_types", []),
            tags=extra.get("tags", []),
            facilities=extra.get("facilities", []),
            semantic_score=candidate.semantic_score,
            matched_query=candidate.matched_query,
            wechat_room_id=extra.get("wechat_room_id", ""),
            lease_room_id=extra.get("lease_room_id"),
            source_collection=extra.get("source_collection", ""),
            source_record_id=extra.get("source_record_id", ""),
            lease_validation_status="not_checked",
            evidence_level=evidence_level,
        ))

    if diagnostic is not None:
        diagnostic.lease_validated_count = len(lease_validated_ids)
        diagnostic.lease_validation_failed_count = len(lease_mappable) - len(lease_validated_ids)
        diagnostic.demo_fallback_count = len(wechat_only)
        diagnostic.lease_dropped_room_ids = []
    if not validated:
        if diagnostic is not None:
            diagnostic.failure_stage = "lease_validation_empty"
        return []
    preference_scores = preference_scorer.score(plan.raw_message, plan.soft_preferences, validated)
    if diagnostic is not None:
        diagnostic.preference_scored_count = len(preference_scores) if preference_scores else 0
    ranked = rank_rooms(validated, plan, preference_scores, top_n=top_n)
    if diagnostic is not None:
        diagnostic.ranked_count = len(ranked)
        diagnostic.final_room_ids = [r.room_id for r in ranked]
        for r in ranked:
            diagnostic.score_breakdown.append({
                "room_id": r.room_id,
                "final_score": getattr(r, "final_score", None),
                "semantic_score": getattr(r, "semantic_score", None),
                "preference_score": getattr(r, "preference_score", None),
            })
        if not ranked:
            diagnostic.failure_stage = "ranking_empty"
    return ranked


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)
