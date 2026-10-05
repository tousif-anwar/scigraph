from scigraph.preprocessing.quality import run_quality_checks


EXPECTED_FIELDS = [
    "id",
    "doi",
    "title",
    "display_name",
    "publication_date",
    "publication_year",
    "type",
    "authorships",
    "primary_location",
    "referenced_works",
    "abstract_inverted_index",
    "language",
    "open_access",
]


def _check(payload, name: str) -> dict:
    return next(check for check in payload["checks"] if check["name"] == name)


def test_quality_checks_detect_core_issues() -> None:
    records = [
        {
            "id": "https://openalex.org/W1",
            "doi": "https://doi.org/10.123/example",
            "title": "Good record",
            "display_name": "Good record",
            "publication_date": "2024-01-02",
            "publication_year": 2024,
            "type": "article",
            "authorships": [{"author": {"id": "https://openalex.org/A1"}}],
            "primary_location": {"source": {"id": "https://openalex.org/S1"}},
            "locations": [],
            "cited_by_count": 3,
            "referenced_works": ["https://openalex.org/W0"],
            "abstract_inverted_index": {"Good": [0], "record": [1]},
            "language": "en",
            "open_access": {"is_oa": True},
        },
        {
            "id": "bad-id",
            "doi": "not-a-doi",
            "title": "",
            "display_name": None,
            "publication_date": "2024-13-99",
            "publication_year": 2023,
            "type": "article",
            "authorships": [],
            "primary_location": {},
            "locations": {},
            "cited_by_count": -1,
            "referenced_works": [],
            "abstract_inverted_index": {"bad": ["zero"]},
            "language": None,
            "open_access": [],
        },
    ]

    payload = run_quality_checks(records, EXPECTED_FIELDS)

    assert _check(payload, "malformed_openalex_ids")["count"] == 1
    assert _check(payload, "missing_titles")["count"] == 1
    assert _check(payload, "malformed_publication_dates")["count"] == 1
    assert _check(payload, "missing_authorships")["count"] == 1
    assert _check(payload, "malformed_abstract_index")["count"] == 1
    assert _check(payload, "invalid_cited_by_count")["count"] == 1
    assert _check(payload, "malformed_locations")["count"] == 1
    assert _check(payload, "malformed_open_access")["count"] == 1


def test_quality_checks_detect_duplicates_and_schema_drift() -> None:
    records = [
        {
            "id": "https://openalex.org/W1",
            "publication_date": "2024-01-01",
            "publication_year": 2024,
            "authorships": [{"author": {"id": "A1"}}, {"author": {"id": "A1"}}],
            "referenced_works": ["https://openalex.org/W2", "https://openalex.org/W2"],
            "unexpected": "field",
        },
        {
            "id": "https://openalex.org/W1",
            "publication_date": "2024-01-01",
            "publication_year": 2024,
            "authorships": [],
            "referenced_works": ["https://openalex.org/W1"],
        },
    ]

    payload = run_quality_checks(records, ["id", "publication_date", "publication_year"])

    assert _check(payload, "duplicate_ids")["count"] == 2
    assert _check(payload, "unexpected_fields")["count"] >= 1
    assert _check(payload, "duplicate_author_ids_within_paper")["count"] == 1
    assert _check(payload, "duplicate_references_within_paper")["count"] == 1
    assert _check(payload, "self_references")["count"] == 1
