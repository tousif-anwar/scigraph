"""Pure normalization helpers shared by tests and Spark pipeline design."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from scigraph.ingestion.openalex import reconstruct_abstract

OPENALEX_PREFIX = "https://openalex.org/"
WHITESPACE_RE = re.compile(r"\s+")
NON_WORD_SPACE_RE = re.compile(r"[^\w\s]", re.UNICODE)


def normalize_whitespace(value: str | None) -> str | None:
    """Trim and collapse whitespace in text values."""
    if value is None:
        return None
    normalized = WHITESPACE_RE.sub(" ", value).strip()
    return normalized or None


def normalize_text_for_analysis(value: str | None) -> str | None:
    """Create a lowercase, punctuation-light text field for later analytics."""
    normalized = normalize_whitespace(value)
    if normalized is None:
        return None
    normalized = NON_WORD_SPACE_RE.sub(" ", normalized.lower())
    normalized = WHITESPACE_RE.sub(" ", normalized).strip()
    return normalized or None


def short_openalex_id(value: str | None) -> str | None:
    """Convert an OpenAlex URL identifier to its compact ID where possible."""
    if not value:
        return None
    return value.removeprefix(OPENALEX_PREFIX)


def normalize_doi(value: str | None) -> str | None:
    """Normalize DOI strings to lowercase URL form where possible."""
    if value is None:
        return None
    value = value.strip().lower()
    if not value:
        return None
    if value.startswith("https://doi.org/"):
        return value
    if value.startswith("doi:"):
        return f"https://doi.org/{value[4:]}"
    if value.startswith("10."):
        return f"https://doi.org/{value}"
    return value


def parse_year_from_date(value: str | None) -> int | None:
    """Parse the year from an ISO publication date."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").year
    except ValueError:
        return None


def validation_flags(record: dict[str, Any]) -> list[str]:
    """Return record-level validation flags for Silver-stage accounting."""
    flags: list[str] = []
    if not record.get("id"):
        flags.append("missing_id")
    if not record.get("title") and not record.get("display_name"):
        flags.append("missing_title")
    if not record.get("abstract_inverted_index"):
        flags.append("missing_abstract")
    if not record.get("authorships"):
        flags.append("missing_authorships")
    if not isinstance(record.get("referenced_works", []), list):
        flags.append("malformed_references")

    publication_year = record.get("publication_year")
    parsed_year = parse_year_from_date(record.get("publication_date"))
    if parsed_year is None:
        flags.append("malformed_publication_date")
    elif isinstance(publication_year, int) and publication_year != parsed_year:
        flags.append("publication_year_mismatch")
    elif not isinstance(publication_year, int):
        flags.append("missing_publication_year")

    return flags


def normalize_publication_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize one OpenAlex record into the Silver publication shape."""
    title = normalize_whitespace(record.get("title") or record.get("display_name"))
    abstract = reconstruct_abstract(record.get("abstract_inverted_index"))
    referenced_works = record.get("referenced_works") or []
    authorships = record.get("authorships") or []
    concepts = record.get("concepts") or []
    topics = record.get("topics") or []

    primary_location = record.get("primary_location") or {}
    source = primary_location.get("source") if isinstance(primary_location, dict) else None
    source = source if isinstance(source, dict) else {}

    return {
        "paper_id": record.get("id"),
        "paper_openalex_id": short_openalex_id(record.get("id")),
        "doi": normalize_doi(record.get("doi")),
        "title": title,
        "title_normalized": normalize_text_for_analysis(title),
        "abstract": abstract,
        "abstract_available": abstract is not None,
        "publication_date": record.get("publication_date"),
        "publication_year": record.get("publication_year"),
        "document_type": record.get("type"),
        "language": record.get("language"),
        "cited_by_count": record.get("cited_by_count"),
        "source_id": source.get("id"),
        "source_name": source.get("display_name"),
        "reference_count": len(referenced_works) if isinstance(referenced_works, list) else 0,
        "author_count": len(authorships) if isinstance(authorships, list) else 0,
        "concept_count": len(concepts) if isinstance(concepts, list) else 0,
        "topic_count": len(topics) if isinstance(topics, list) else 0,
        "quality_flags": validation_flags(record),
    }
