import pytest

from scigraph.ranking.composite import safe_minmax, weighted_score


def test_weighted_score() -> None:
    assert weighted_score({"a": 1.0, "b": 0.5}, {"a": 0.4, "b": 0.6}) == pytest.approx(0.7)


def test_weighted_score_missing_component_is_zero() -> None:
    assert weighted_score({"a": 1.0}, {"a": 0.4, "b": 0.6}) == pytest.approx(0.4)


def test_safe_minmax() -> None:
    assert safe_minmax(5, 0, 10) == pytest.approx(0.5)
    assert safe_minmax(5, 5, 5) == 0.0
