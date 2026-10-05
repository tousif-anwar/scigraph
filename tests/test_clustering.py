from scigraph.text.clustering import choose_best_k, cluster_size_distribution


def test_choose_best_k_by_silhouette() -> None:
    assert choose_best_k(
        [
            {"k": 3, "silhouette": 0.1},
            {"k": 5, "silhouette": 0.4},
            {"k": 8, "silhouette": 0.2},
        ]
    ) == 5


def test_cluster_size_distribution() -> None:
    assert cluster_size_distribution([2, 1, 2, 0, 1, 1]) == {0: 1, 1: 3, 2: 2}
