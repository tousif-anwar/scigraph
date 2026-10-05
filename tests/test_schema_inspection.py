import json

from scigraph.ingestion.inspect_schema import dataset_statistics, load_jsonl, summarize_schema


def test_schema_summary_from_jsonl(tmp_path) -> None:
    path = tmp_path / "sample.jsonl"
    records = [
        {
            "id": "https://openalex.org/W1",
            "title": "Distributed systems",
            "publication_year": 2024,
            "authorships": [{"author": {"id": "https://openalex.org/A1"}}],
            "referenced_works": ["https://openalex.org/W0"],
            "abstract_inverted_index": {"Distributed": [0], "systems": [1]},
            "type": "article",
            "concepts": [{"display_name": "Computer science"}],
        },
        {
            "id": "https://openalex.org/W2",
            "title": None,
            "publication_year": 2025,
            "authorships": [],
            "referenced_works": [],
            "abstract_inverted_index": None,
            "type": "article",
            "concepts": [],
        },
    ]
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    loaded = load_jsonl(path)
    summary = summarize_schema(loaded)
    stats = dataset_statistics(loaded)

    title_field = next(field for field in summary["fields"] if field["field"] == "title")
    assert title_field["null_percentage"] == 50.0
    assert stats["record_count"] == 2
    assert stats["unique_authors"] == 1
    assert stats["reference_count"] == 1
    assert stats["missing_abstracts"] == 1
