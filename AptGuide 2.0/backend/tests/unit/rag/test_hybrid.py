from aptguide2.rag.hybrid import HybridCandidate, merge_hybrid_candidates, normalize_scores
from aptguide2.rag.sparse import sparse_score


def test_sparse_score_rewards_token_overlap_without_being_the_only_signal():
    score = sparse_score("押金退还多久到账", "押金退还规则")

    assert 0.0 < score <= 1.0


def test_normalize_scores_handles_equal_values():
    assert normalize_scores([0.5, 0.5]) == [1.0, 1.0]


def test_merge_hybrid_candidates_dedupes_and_preserves_channels():
    dense = [
        HybridCandidate(id="KB-LEASE-005#01", dense_score=0.82, channel="dense", payload={"doc_id": "KB-LEASE-005"}),
    ]
    sparse = [
        HybridCandidate(id="KB-LEASE-005#01", sparse_score=0.6, channel="sparse", payload={"doc_id": "KB-LEASE-005"}),
        HybridCandidate(id="KB-PAY-001#01", sparse_score=0.7, channel="sparse", payload={"doc_id": "KB-PAY-001"}),
    ]

    merged = merge_hybrid_candidates([dense, sparse])

    assert [c.id for c in merged] == ["KB-LEASE-005#01", "KB-PAY-001#01"]
    assert set(merged[0].recall_channels) == {"dense", "sparse"}
    assert merged[0].dense_score == 0.82
    assert merged[0].sparse_score == 0.6
