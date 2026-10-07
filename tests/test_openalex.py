from scigraph.ingestion.acquire_openalex import build_openalex_url
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


def test_build_openalex_url_uses_cursor_without_sample() -> None:
    config = {
        "dataset": {
            "api_page_size": 200,
            "contact_email": "",
            "filters": {"from_publication_date": "2010-01-01", "has_abstract": True, "type": "article"},
            "sample_size": 1_000_000,
            "seed": 660,
            "select_fields": ["id", "title"],
            "source_url": "https://api.openalex.org/works",
        }
    }

    url = build_openalex_url(config, cursor="*")

    assert "cursor=%2A" in url
    assert "per-page=200" in url
    assert "sample=" not in url
    assert "seed=" not in url
