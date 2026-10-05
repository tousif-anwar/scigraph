import pytest

from scigraph.graph.citation_graph import degree_ratio, pagerank_base_score


def test_pagerank_base_score() -> None:
    assert pagerank_base_score(10, 0.85) == pytest.approx(0.015)


def test_pagerank_base_score_rejects_empty_graph() -> None:
    with pytest.raises(ValueError):
        pagerank_base_score(0, 0.85)


def test_degree_ratio_smooths_zero_indegree() -> None:
    assert degree_ratio(0.25, 0) == 0.25
    assert degree_ratio(0.25, 4) == 0.05
