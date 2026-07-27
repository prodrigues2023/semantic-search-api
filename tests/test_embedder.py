import math

from search_api.embedder import embed


def test_embedding_is_deterministic():
    assert embed("why is my payment failing") == embed("why is my payment failing")


def test_embedding_is_unit_normalised():
    vec = embed("refund policy")
    norm = math.sqrt(sum(v * v for v in vec))
    assert abs(norm - 1.0) < 1e-9


def test_synonyms_land_in_the_same_buckets():
    a = embed("the transaction is failing")
    b = embed("the payment was declined")
    dot = sum(x * y for x, y in zip(a, b))
    assert dot > 0.3
