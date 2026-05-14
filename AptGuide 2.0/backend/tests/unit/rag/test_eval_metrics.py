from aptguide2.rag.eval_metrics import hit_at_k, mean_reciprocal_rank, ndcg_at_k


def test_hit_at_k_true_when_expected_item_in_top_k():
    assert hit_at_k(["a", "b", "c"], {"c"}, 3) is True
    assert hit_at_k(["a", "b", "c"], {"c"}, 2) is False


def test_mrr_uses_first_relevant_rank():
    assert mean_reciprocal_rank(["a", "b", "c"], {"c"}) == 1 / 3


def test_ndcg_at_k_is_one_for_perfect_first_result():
    assert ndcg_at_k(["a", "b"], {"a"}, 2) == 1.0
