from search_api.metrics import ndcg_at_k, recall_at_k


def test_perfect_ranking_scores_one():
    judgments = {"a": 3, "b": 2, "c": 1}
    assert ndcg_at_k(["a", "b", "c"], judgments, 10) == 1.0
    assert recall_at_k(["a", "b", "c"], judgments, 10) == 1.0


def test_reversed_ranking_scores_below_one():
    judgments = {"a": 3, "b": 2, "c": 1}
    assert ndcg_at_k(["c", "b", "a"], judgments, 10) < 1.0


def test_missing_relevant_chunk_hurts_recall():
    judgments = {"a": 3, "b": 2}
    assert recall_at_k(["a", "x", "y"], judgments, 10) == 0.5


def test_zero_relevant_query_scores_one_not_zero():
    assert ndcg_at_k(["x", "y"], {}, 10) == 1.0
    assert recall_at_k(["x", "y"], {}, 10) == 1.0


def test_k_truncates_the_ranked_list():
    judgments = {"a": 3, "b": 2, "c": 1}
    assert recall_at_k(["x", "x", "a"], judgments, 2) == 0.0
    assert abs(recall_at_k(["x", "x", "a"], judgments, 3) - (1 / 3)) < 1e-9
