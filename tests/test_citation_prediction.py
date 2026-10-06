import pytest

from scigraph.evaluation.citation_prediction import high_citation_label, majority_baseline_accuracy


def test_high_citation_label() -> None:
    assert high_citation_label(10, 10) == 1
    assert high_citation_label(9, 10) == 0


def test_majority_baseline_accuracy() -> None:
    assert majority_baseline_accuracy(25, 75) == pytest.approx(0.75)
    assert majority_baseline_accuracy(0, 0) == 0.0
