import pytest

from scigraph.retrieval.sparse import precision_at_k, tokenize_query


def test_tokenize_query_uses_text_rules() -> None:
    assert tokenize_query("AI in healthcare, and education!") == ["healthcare", "education"]


def test_precision_at_k() -> None:
    assert precision_at_k(3, 10) == pytest.approx(0.3)


def test_precision_at_k_rejects_invalid_k() -> None:
    with pytest.raises(ValueError):
        precision_at_k(1, 0)
