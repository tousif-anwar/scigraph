import pytest

from scigraph.graph.author_collaboration import collaboration_density, ordered_author_pair


def test_ordered_author_pair_is_deterministic() -> None:
    assert ordered_author_pair("B", "A") == ("A", "B")
    assert ordered_author_pair("A", "B") == ("A", "B")


def test_ordered_author_pair_rejects_self_pair() -> None:
    with pytest.raises(ValueError):
        ordered_author_pair("A", "A")


def test_collaboration_density() -> None:
    assert collaboration_density(3, 3) == pytest.approx(1.0)
    assert collaboration_density(1, 4) == pytest.approx(1 / 6)
    assert collaboration_density(5, 1) == 0.0
