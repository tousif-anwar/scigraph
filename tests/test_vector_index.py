from scigraph.retrieval.vector_index import backend_available, choose_backend, normalize_query


def test_normalize_query_collapses_whitespace():
    assert normalize_query("  graph   neural\n retrieval  ") == "graph neural retrieval"


def test_choose_backend_falls_back_for_missing_optional_backend():
    chosen = choose_backend("auto")
    assert chosen in {"chroma", "faiss", "sklearn_tfidf_fallback"}


def test_backend_available_returns_bool():
    assert isinstance(backend_available("sys"), bool)
