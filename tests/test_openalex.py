from scigraph.ingestion.openalex import nested_get, reconstruct_abstract


def test_reconstruct_abstract_orders_tokens() -> None:
    inverted_index = {"scale": [2], "Data": [0], "matters": [3], "at": [1]}

    assert reconstruct_abstract(inverted_index) == "Data at scale matters"


def test_reconstruct_abstract_handles_missing() -> None:
    assert reconstruct_abstract(None) is None
    assert reconstruct_abstract({}) is None


def test_nested_get() -> None:
    record = {"primary_location": {"source": {"display_name": "Example Journal"}}}

    assert nested_get(record, "primary_location.source.display_name") == "Example Journal"
    assert nested_get(record, "primary_location.missing.display_name") is None
