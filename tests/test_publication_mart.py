import pytest

from scigraph.features.publication_mart import completeness_rate, safe_average


def test_completeness_rate() -> None:
    assert completeness_rate(25, 100) == pytest.approx(0.25)
    assert completeness_rate(1, 0) == 0.0


def test_safe_average() -> None:
    assert safe_average(10, 4) == pytest.approx(2.5)
    assert safe_average(10, 0) == 0.0
