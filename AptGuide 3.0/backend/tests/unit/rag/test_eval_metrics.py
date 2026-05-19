from __future__ import annotations

import math

import pytest

from aptguide3.rag.eval_metrics import hit_at_k, mean_reciprocal_rank, ndcg_at_k


class TestHitAtK:
    def test_hit_within_k(self):
        assert hit_at_k(["a", "b", "c"], {"b"}, 2) is True

    def test_miss_outside_k(self):
        assert hit_at_k(["a", "b", "c"], {"c"}, 2) is False

    def test_hit_at_exact_k(self):
        assert hit_at_k(["a", "b", "c"], {"c"}, 3) is True

    def test_empty_expected(self):
        assert hit_at_k(["a", "b"], set(), 5) is False

    def test_empty_actual(self):
        assert hit_at_k([], {"a"}, 5) is False

    def test_both_empty(self):
        assert hit_at_k([], set(), 5) is False

    def test_multiple_matches(self):
        assert hit_at_k(["a", "b", "c"], {"a", "c"}, 2) is True


class TestMeanReciprocalRank:
    def test_first_rank(self):
        assert mean_reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0

    def test_second_rank(self):
        assert mean_reciprocal_rank(["a", "b", "c"], {"b"}) == 0.5

    def test_third_rank(self):
        assert mean_reciprocal_rank(["a", "b", "c"], {"c"}) == pytest.approx(1 / 3)

    def test_no_match(self):
        assert mean_reciprocal_rank(["a", "b", "c"], {"d"}) == 0.0

    def test_empty_actual(self):
        assert mean_reciprocal_rank([], {"a"}) == 0.0

    def test_empty_expected(self):
        assert mean_reciprocal_rank(["a", "b"], set()) == 0.0

    def test_multiple_expected_returns_best(self):
        # "b" is rank 2 -> 0.5, "a" is rank 1 -> 1.0; best is 1.0
        assert mean_reciprocal_rank(["a", "b", "c"], {"a", "b"}) == 1.0


class TestNDCGAtK:
    def test_perfect_ranking(self):
        # All expected items at top positions
        result = ndcg_at_k(["a", "b", "c"], {"a", "b", "c"}, 3)
        assert result == 1.0

    def test_partial_ranking(self):
        # Only one hit out of three expected
        result = ndcg_at_k(["a", "x", "y"], {"a", "b", "c"}, 3)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, 4))
        dcg = 1.0 / math.log2(2)  # rank 1
        expected = round(dcg / idcg, 6)
        assert result == expected

    def test_no_match(self):
        assert ndcg_at_k(["a", "b", "c"], {"d", "e"}, 3) == 0.0

    def test_empty_expected(self):
        assert ndcg_at_k(["a", "b"], set(), 5) == 0.0

    def test_empty_actual(self):
        assert ndcg_at_k([], {"a"}, 5) == 0.0

    def test_k_limits_evaluation(self):
        # k=1, expected has 3 items, only first matters
        result = ndcg_at_k(["a", "x", "x"], {"a", "b", "c"}, 1)
        assert result == 1.0  # dcg=1/log2(2)=1, idcg=1/log2(2)=1

    def test_imperfect_ranking_with_k(self):
        # Expected items not at top
        result = ndcg_at_k(["x", "a", "b"], {"a", "b", "c"}, 2)
        # k=2, only positions 1 and 2 considered; "x" at rank 1 (not expected), "a" at rank 2
        dcg = 1.0 / math.log2(3)  # rank 2 hit
        ideal_hits = min(3, 2)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
        expected = round(dcg / idcg, 6)
        assert result == expected
