import pytest

from scigraph.retrieval.advanced import (
    average_precision_at_k,
    cosine_similarity,
    ndcg_at_k,
    reciprocal_rank,
)


def test_cosine_similarity() -> None:
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([0, 0], [1, 0]) == 0.0


def test_reciprocal_rank() -> None:
    assert reciprocal_rank(1, 60) == pytest.approx(1 / 61)
    with pytest.raises(ValueError):
        reciprocal_rank(0, 60)


def test_ndcg_at_k() -> None:
    assert ndcg_at_k([1, 0, 1], 3) > 0
    assert ndcg_at_k([0, 0, 0], 3) == 0.0


def test_average_precision_at_k() -> None:
    assert average_precision_at_k([1, 0, 1], 3) == pytest.approx((1 / 1 + 2 / 3) / 2)
    assert average_precision_at_k([0, 0], 2) == 0.0
