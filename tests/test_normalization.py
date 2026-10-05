from scigraph.preprocessing.normalization import (
    normalize_doi,
    normalize_publication_record,
    normalize_text_for_analysis,
    short_openalex_id,
    validation_flags,
)


def test_normalize_doi_to_url_form() -> None:
    assert normalize_doi("10.123/ABC") == "https://doi.org/10.123/abc"
    assert normalize_doi("doi:10.123/ABC") == "https://doi.org/10.123/abc"
    assert normalize_doi("https://doi.org/10.123/ABC") == "https://doi.org/10.123/abc"
    assert normalize_doi("  ") is None


def test_normalize_text_for_analysis() -> None:
    assert normalize_text_for_analysis("  A Study: Data-at-Scale!  ") == "a study data at scale"


def test_short_openalex_id() -> None:
    assert short_openalex_id("https://openalex.org/W123") == "W123"
    assert short_openalex_id("W123") == "W123"


def test_validation_flags_detect_record_issues() -> None:
    record = {
        "id": "https://openalex.org/W1",
        "title": "",
        "display_name": None,
        "publication_date": "2024-01-02",
        "publication_year": 2023,
        "authorships": [],
        "referenced_works": {},
        "abstract_inverted_index": None,
    }

    assert validation_flags(record) == [
        "missing_title",
        "missing_abstract",
        "missing_authorships",
        "malformed_references",
        "publication_year_mismatch",
    ]


def test_normalize_publication_record() -> None:
    record = {
        "id": "https://openalex.org/W1",
        "doi": "10.123/ABC",
        "title": "  Example Paper ",
        "display_name": "Ignored",
        "abstract_inverted_index": {"Scale": [2], "Data": [0], "at": [1]},
        "publication_date": "2024-01-02",
        "publication_year": 2024,
        "type": "article",
        "language": "en",
        "cited_by_count": 5,
        "primary_location": {"source": {"id": "https://openalex.org/S1", "display_name": "Venue"}},
        "referenced_works": ["https://openalex.org/W0"],
        "authorships": [{"author": {"id": "https://openalex.org/A1"}}],
        "concepts": [],
        "topics": [{"id": "https://openalex.org/T1"}],
    }

    normalized = normalize_publication_record(record)

    assert normalized["paper_openalex_id"] == "W1"
    assert normalized["doi"] == "https://doi.org/10.123/abc"
    assert normalized["title"] == "Example Paper"
    assert normalized["title_normalized"] == "example paper"
    assert normalized["abstract"] == "Data at Scale"
    assert normalized["reference_count"] == 1
    assert normalized["author_count"] == 1
    assert normalized["quality_flags"] == []
