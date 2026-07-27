from search_api.ranking import fuse


def test_doc_ranked_first_in_both_lists_wins():
    lexical = ["a", "b", "c"]
    semantic = ["a", "c", "b"]
    fused = fuse(lexical, semantic)
    ranked = sorted(fused, key=lambda cid: -fused[cid]["score"])
    assert ranked[0] == "a"


def test_score_is_in_zero_to_one_range():
    fused = fuse(["a", "b"], ["b", "c"])
    for entry in fused.values():
        assert 0 < entry["score"] <= 1


def test_absent_from_one_list_still_present():
    fused = fuse(["a", "b"], [])
    assert fused["a"]["semanticRank"] is None
    assert fused["a"]["lexicalRank"] == 1


def test_single_list_top_rank_reaches_max_score():
    fused = fuse(["a"], [])
    assert fused["a"]["score"] == 1.0
