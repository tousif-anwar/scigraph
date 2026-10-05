"""Inspect observed JSONL schema and generate the initial data dictionary."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from scigraph.utils.config import load_config, resolve_project_path

FIELD_MEANINGS: dict[str, str] = {
    "id": "Stable OpenAlex work identifier.",
    "doi": "Digital Object Identifier when available.",
    "title": "Publication title.",
    "display_name": "OpenAlex display name for the work; often equivalent to title.",
    "publication_date": "Publication date as provided by OpenAlex.",
    "publication_year": "Publication year as provided by OpenAlex.",
    "type": "OpenAlex work type, such as article.",
    "authorships": "Nested authorship records containing author and affiliation metadata.",
    "primary_location": "Primary source/location metadata for the work.",
    "locations": "All known source/location records for the work.",
    "cited_by_count": "Number of works OpenAlex records as citing this work.",
    "referenced_works": "OpenAlex work IDs cited by this work.",
    "concepts": "Legacy OpenAlex concept tags with scores.",
    "topics": "OpenAlex topic classifications when available.",
    "abstract_inverted_index": "OpenAlex abstract represented as an inverted index, not plaintext.",
    "language": "Detected language code when available.",
    "open_access": "Open access status metadata.",
}

USED_FIELDS: set[str] = {
    "id",
    "doi",
    "title",
    "display_name",
    "publication_date",
    "publication_year",
    "type",
    "authorships",
    "primary_location",
    "cited_by_count",
    "referenced_works",
    "concepts",
    "topics",
    "abstract_inverted_index",
    "language",
    "open_access",
}

QUALITY_NOTES: dict[str, str] = {
    "doi": "May be null or inconsistently formatted.",
    "title": "May be missing, duplicated, or contain source encoding artifacts.",
    "display_name": "May duplicate title and should not be treated as an independent text field.",
    "publication_date": "Can be null or less precise in source metadata.",
    "publication_year": "Should be validated for plausible range.",
    "authorships": "Nested structure may be empty; author identity resolution is imperfect.",
    "primary_location": "Nested venue/source metadata can be missing.",
    "locations": "Can be large and nested; not all locations have complete license/source data.",
    "referenced_works": "May be empty even for papers with bibliographies outside OpenAlex coverage.",
    "concepts": "Legacy field; useful for early analysis but should be interpreted carefully.",
    "topics": "May be absent for some records depending on OpenAlex coverage.",
    "abstract_inverted_index": "Can be null; reconstructing text requires position ordering.",
    "language": "Detected language can be missing or imperfect.",
    "open_access": "Availability and license metadata may differ by location.",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL records from disk."""
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def type_name(value: Any) -> str:
    """Return a concise JSON-oriented type name."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def compact_example(value: Any, max_length: int = 140) -> str:
    """Create a compact markdown-safe example value."""
    if value is None:
        return "`null`"
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = text.replace("\n", " ")
    if len(text) > max_length:
        text = text[: max_length - 3] + "..."
    escaped = text.replace("|", "\\|")
    return f"`{escaped}`"


def summarize_schema(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize top-level observed fields."""
    total = len(records)
    fields = sorted({field for record in records for field in record})
    summary: dict[str, Any] = {"record_count": total, "fields": []}

    for field in fields:
        values = [record.get(field) for record in records]
        missing = sum(1 for value in values if value is None)
        observed_values = [value for value in values if value is not None]
        type_counts = Counter(type_name(value) for value in values)
        example = next((value for value in observed_values if value not in ("", [], {})), None)
        if example is None and observed_values:
            example = observed_values[0]

        summary["fields"].append(
            {
                "field": field,
                "types": dict(sorted(type_counts.items())),
                "meaning": FIELD_MEANINGS.get(field, "Observed OpenAlex field; needs further review."),
                "null_count": missing,
                "null_percentage": round((missing / total * 100) if total else 0.0, 2),
                "example": example,
                "used": field in USED_FIELDS,
                "quality_issues": QUALITY_NOTES.get(field, "No specific issue identified yet."),
            }
        )

    return summary


def dataset_statistics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute small dataset-level statistics for Milestone 1 documentation."""
    years = [record.get("publication_year") for record in records if record.get("publication_year")]
    work_ids = [record.get("id") for record in records if record.get("id")]
    author_ids: set[str] = set()
    reference_count = 0
    documents_per_year: Counter[int] = Counter()
    document_types: Counter[str] = Counter()
    missing_titles = 0
    missing_abstracts = 0
    missing_authors = 0
    concept_counts: Counter[str] = Counter()

    for record in records:
        year = record.get("publication_year")
        if isinstance(year, int):
            documents_per_year[year] += 1
        if record.get("type"):
            document_types[str(record["type"])] += 1
        if not record.get("title") and not record.get("display_name"):
            missing_titles += 1
        if not record.get("abstract_inverted_index"):
            missing_abstracts += 1
        authorships = record.get("authorships") or []
        if not authorships:
            missing_authors += 1
        for authorship in authorships:
            author = authorship.get("author") if isinstance(authorship, dict) else None
            author_id = author.get("id") if isinstance(author, dict) else None
            if author_id:
                author_ids.add(author_id)
        references = record.get("referenced_works") or []
        if isinstance(references, list):
            reference_count += len(references)
        for concept in record.get("concepts") or []:
            if isinstance(concept, dict) and concept.get("display_name"):
                concept_counts[str(concept["display_name"])] += 1

    duplicate_identifiers = len(work_ids) - len(set(work_ids))
    date_range = [min(years), max(years)] if years else [None, None]
    return {
        "record_count": len(records),
        "unique_publications": len(set(work_ids)),
        "unique_authors": len(author_ids),
        "reference_count": reference_count,
        "date_range_publication_year": date_range,
        "documents_per_year": dict(sorted(documents_per_year.items())),
        "missing_abstracts": missing_abstracts,
        "missing_titles": missing_titles,
        "missing_authors": missing_authors,
        "duplicate_identifiers": duplicate_identifiers,
        "document_types": dict(document_types.most_common()),
        "top_concepts": dict(concept_counts.most_common(20)),
    }


def write_data_dictionary(summary: dict[str, Any], stats: dict[str, Any], output_path: Path) -> None:
    """Write a markdown data dictionary from observed schema summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Data Dictionary",
        "",
        f"Generated from observed OpenAlex sample records on {date.today().isoformat()}.",
        "",
        "## Dataset Summary",
        "",
        f"- Records inspected: {stats['record_count']}",
        f"- Unique publication IDs: {stats['unique_publications']}",
        f"- Unique author IDs observed: {stats['unique_authors']}",
        f"- Referenced works counted: {stats['reference_count']}",
        f"- Publication-year range: {stats['date_range_publication_year']}",
        f"- Missing abstracts: {stats['missing_abstracts']}",
        f"- Missing titles: {stats['missing_titles']}",
        f"- Missing authors: {stats['missing_authors']}",
        f"- Duplicate publication IDs: {stats['duplicate_identifiers']}",
        "",
        "## Observed Fields",
        "",
        "| field | type | meaning | null % | example | used? | known quality issues |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]

    for field in summary["fields"]:
        types = ", ".join(f"{name} ({count})" for name, count in field["types"].items())
        used = "yes" if field["used"] else "no"
        lines.append(
            "| {field} | {types} | {meaning} | {null_percentage:.2f} | {example} | {used} | {quality_issues} |".format(
                field=field["field"],
                types=types,
                meaning=field["meaning"].replace("|", "\\|"),
                null_percentage=field["null_percentage"],
                example=compact_example(field["example"]),
                used=used,
                quality_issues=field["quality_issues"].replace("|", "\\|"),
            )
        )

    lines.extend(
        [
            "",
            "## Dataset Statistics",
            "",
            "Machine-readable statistics are saved to `reports/results/schema_summary.json`.",
            "",
            "Document types:",
            "",
            "```json",
            json.dumps(stats["document_types"], indent=2, sort_keys=True),
            "```",
            "",
            "Top observed concepts:",
            "",
            "```json",
            json.dumps(stats["top_concepts"], indent=2, sort_keys=True),
            "```",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def inspect_schema(config: dict[str, Any]) -> dict[str, Any]:
    """Load the raw sample, summarize schema, and write outputs."""
    raw_jsonl_path = resolve_project_path(config, config["paths"]["raw_sample_jsonl"])
    summary_path = resolve_project_path(config, config["paths"]["schema_summary_json"])
    dictionary_path = resolve_project_path(config, config["paths"]["data_dictionary_md"])

    records = load_jsonl(raw_jsonl_path)
    summary = summarize_schema(records)
    stats = dataset_statistics(records)
    payload = {"schema": summary, "dataset_statistics": stats}

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_data_dictionary(summary, stats, dictionary_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    payload = inspect_schema(config)
    print(json.dumps(payload["dataset_statistics"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
