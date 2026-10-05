import pytest

from scigraph.temporal.trends import citation_rate, year_over_year_growth


def test_year_over_year_growth() -> None:
    assert year_over_year_growth(15, 10) == pytest.approx(0.5)
    assert year_over_year_growth(5, 10) == pytest.approx(-0.5)


def test_year_over_year_growth_without_baseline() -> None:
    assert year_over_year_growth(10, 0) is None
    assert year_over_year_growth(10, None) is None


def test_citation_rate() -> None:
    assert citation_rate(25, 5) == pytest.approx(5.0)
    assert citation_rate(25, 0) == 0.0
