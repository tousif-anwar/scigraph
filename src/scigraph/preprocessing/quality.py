"""Data-quality checks for raw OpenAlex work records."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from scigraph.ingestion.inspect_schema import load_jsonl
from scigraph.utils.config import load_config, resolve_project_path

OPENALEX_WORK_ID_RE = re.compile(r"^https://openalex\.org/W\d+$")
DOI_RE = re.compile(r"^(https://doi\.org/)?10\.\S+/\S+$", re.IGNORECASE)


@dataclass(frozen=True)
class QualityCheck:
    """A single data-quality check result."""

    name: str
    category: str
    severity: str
    count: int
    denominator: int
    description: str
    examples: tuple[str, ...] = ()

    @property
    def percentage(self) -> float:
        if self.denominator == 0:
            return 0.0
        return round(self.count / self.denominator * 100, 2)

    @property
    def status(self) -> str:
        return "pass" if self.count == 0 else self.severity

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "severity": self.severity,
            "status": self.status,
            "count": self.count,
            "denominator": self.denominator,
            "percentage": self.percentage,
            "description": self.description,
            "examples": list(self.examples),
        }


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _example_ids(records: list[dict[str, Any]], predicate, limit: int = 5) -> tuple[str, ...]:
    examples: list[str] = []
    for index, record in enumerate(records):
        if predicate(record):
            examples.append(str(record.get("id") or f"record_index:{index}"))
        if len(examples) >= limit:
            break
    return tuple(examples)


def _parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _valid_abstract_index(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    for token, positions in value.items():
        if not isinstance(token, str) or not isinstance(positions, list):
            return False
        if any(not isinstance(position, int) or position < 0 for position in positions):
            return False
    return True


def _author_ids(record: dict[str, Any]) -> list[str]:
    authorships = record.get("authorships")
    if not isinstance(authorships, list):
        return []

    ids: list[str] = []
    for authorship in authorships:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author")
        if isinstance(author, dict) and author.get("id"):
            ids.append(str(author["id"]))
    return ids


def _field_type_counts(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(type(record.get(field)).__name__ for record in records))


def run_quality_checks(records: list[dict[str, Any]], expected_fields: list[str]) -> dict[str, Any]:
    """Run data-quality checks without mutating or filtering records."""
    total = len(records)
    observed_fields = sorted({field for record in records for field in record})
    expected_field_set = set(expected_fields)
    observed_field_set = set(observed_fields)
    today = date.today()

    ids = [record.get("id") for record in records]
    duplicate_ids = {
        value
        for value, count in Counter(value for value in ids if not _is_blank(value)).items()
        if count > 1
    }

    checks = [
        QualityCheck(
            name="missing_expected_fields",
            category="schema",
            severity="error",
            count=len(expected_field_set - observed_field_set),
            denominator=max(len(expected_field_set), 1),
            description="Configured fields that were not observed in any raw record.",
            examples=tuple(sorted(expected_field_set - observed_field_set)[:5]),
        ),
        QualityCheck(
            name="unexpected_fields",
            category="schema",
            severity="warn",
            count=len(observed_field_set - expected_field_set),
            denominator=max(len(observed_field_set), 1),
            description="Observed fields that are not declared in the acquisition config.",
            examples=tuple(sorted(observed_field_set - expected_field_set)[:5]),
        ),
        QualityCheck(
            name="missing_ids",
            category="identity",
            severity="error",
            count=sum(1 for record in records if _is_blank(record.get("id"))),
            denominator=total,
            description="Records without a non-empty OpenAlex work ID.",
            examples=_example_ids(records, lambda record: _is_blank(record.get("id"))),
        ),
        QualityCheck(
            name="malformed_openalex_ids",
            category="identity",
            severity="error",
            count=sum(
                1
                for record in records
                if not _is_blank(record.get("id"))
                and not OPENALEX_WORK_ID_RE.match(str(record.get("id")))
            ),
            denominator=total,
            description="Non-empty work IDs that do not match the expected OpenAlex work URL pattern.",
            examples=_example_ids(
                records,
                lambda record: not _is_blank(record.get("id"))
                and not OPENALEX_WORK_ID_RE.match(str(record.get("id"))),
            ),
        ),
        QualityCheck(
            name="duplicate_ids",
            category="identity",
            severity="error",
            count=sum(1 for value in ids if value in duplicate_ids),
            denominator=total,
            description="Records whose OpenAlex work ID appears more than once in the sample.",
            examples=tuple(sorted(str(value) for value in duplicate_ids)[:5]),
        ),
        QualityCheck(
            name="missing_titles",
            category="text",
            severity="warn",
            count=sum(
                1
                for record in records
                if _is_blank(record.get("title")) and _is_blank(record.get("display_name"))
            ),
            denominator=total,
            description="Records missing both title and display_name.",
            examples=_example_ids(
                records,
                lambda record: _is_blank(record.get("title"))
                and _is_blank(record.get("display_name")),
            ),
        ),
        QualityCheck(
            name="missing_or_empty_abstract_index",
            category="text",
            severity="warn",
            count=sum(1 for record in records if not record.get("abstract_inverted_index")),
            denominator=total,
            description="Records without an abstract inverted index.",
            examples=_example_ids(records, lambda record: not record.get("abstract_inverted_index")),
        ),
        QualityCheck(
            name="malformed_abstract_index",
            category="text",
            severity="error",
            count=sum(
                1
                for record in records
                if record.get("abstract_inverted_index")
                and not _valid_abstract_index(record.get("abstract_inverted_index"))
            ),
            denominator=total,
            description="Abstract inverted indexes with unexpected token/position structure.",
            examples=_example_ids(
                records,
                lambda record: bool(record.get("abstract_inverted_index"))
                and not _valid_abstract_index(record.get("abstract_inverted_index")),
            ),
        ),
        QualityCheck(
            name="missing_publication_dates",
            category="temporal",
            severity="warn",
            count=sum(1 for record in records if _is_blank(record.get("publication_date"))),
            denominator=total,
            description="Records missing publication_date.",
            examples=_example_ids(records, lambda record: _is_blank(record.get("publication_date"))),
        ),
        QualityCheck(
            name="malformed_publication_dates",
            category="temporal",
            severity="error",
            count=sum(
                1
                for record in records
                if not _is_blank(record.get("publication_date"))
                and _parse_iso_date(record.get("publication_date")) is None
            ),
            denominator=total,
            description="Non-empty publication_date values that are not YYYY-MM-DD dates.",
            examples=_example_ids(
                records,
                lambda record: not _is_blank(record.get("publication_date"))
                and _parse_iso_date(record.get("publication_date")) is None,
            ),
        ),
        QualityCheck(
            name="future_publication_dates",
            category="temporal",
            severity="warn",
            count=sum(
                1
                for record in records
                if _parse_iso_date(record.get("publication_date")) is not None
                and _parse_iso_date(record.get("publication_date")) > today
            ),
            denominator=total,
            description="Publication dates after the local run date.",
            examples=_example_ids(
                records,
                lambda record: _parse_iso_date(record.get("publication_date")) is not None
                and _parse_iso_date(record.get("publication_date")) > today,
            ),
        ),
        QualityCheck(
            name="publication_year_mismatch",
            category="temporal",
            severity="error",
            count=sum(
                1
                for record in records
                if _parse_iso_date(record.get("publication_date")) is not None
                and isinstance(record.get("publication_year"), int)
                and _parse_iso_date(record.get("publication_date")).year
                != record.get("publication_year")
            ),
            denominator=total,
            description="publication_year does not match the year component of publication_date.",
            examples=_example_ids(
                records,
                lambda record: _parse_iso_date(record.get("publication_date")) is not None
                and isinstance(record.get("publication_year"), int)
                and _parse_iso_date(record.get("publication_date")).year
                != record.get("publication_year"),
            ),
        ),
        QualityCheck(
            name="invalid_publication_year",
            category="temporal",
            severity="error",
            count=sum(
                1
                for record in records
                if not isinstance(record.get("publication_year"), int)
                or record.get("publication_year") < 1800
                or record.get("publication_year") > today.year + 1
            ),
            denominator=total,
            description="publication_year is missing, non-integer, or outside a plausible range.",
            examples=_example_ids(
                records,
                lambda record: not isinstance(record.get("publication_year"), int)
                or record.get("publication_year") < 1800
                or record.get("publication_year") > today.year + 1,
            ),
        ),
        QualityCheck(
            name="missing_authorships",
            category="authors",
            severity="warn",
            count=sum(1 for record in records if not record.get("authorships")),
            denominator=total,
            description="Records with no authorship entries.",
            examples=_example_ids(records, lambda record: not record.get("authorships")),
        ),
        QualityCheck(
            name="malformed_authorships",
            category="authors",
            severity="error",
            count=sum(
                1
                for record in records
                if record.get("authorships") is not None
                and not isinstance(record.get("authorships"), list)
            ),
            denominator=total,
            description="authorships values that are not arrays.",
            examples=_example_ids(
                records,
                lambda record: record.get("authorships") is not None
                and not isinstance(record.get("authorships"), list),
            ),
        ),
        QualityCheck(
            name="authorship_entries_missing_author_id",
            category="authors",
            severity="warn",
            count=sum(
                1
                for record in records
                for authorship in (record.get("authorships") or [])
                if isinstance(authorship, dict)
                and not (
                    isinstance(authorship.get("author"), dict)
                    and not _is_blank(authorship["author"].get("id"))
                )
            ),
            denominator=sum(
                len(record.get("authorships") or [])
                for record in records
                if isinstance(record.get("authorships"), list)
            ),
            description="Individual authorship entries missing nested author.id.",
        ),
        QualityCheck(
            name="duplicate_author_ids_within_paper",
            category="authors",
            severity="warn",
            count=sum(
                1
                for record in records
                if len(_author_ids(record)) != len(set(_author_ids(record)))
            ),
            denominator=total,
            description="Records with repeated author IDs inside one paper.",
            examples=_example_ids(
                records,
                lambda record: len(_author_ids(record)) != len(set(_author_ids(record))),
            ),
        ),
        QualityCheck(
            name="malformed_referenced_works",
            category="references",
            severity="error",
            count=sum(
                1
                for record in records
                if record.get("referenced_works") is not None
                and not isinstance(record.get("referenced_works"), list)
            ),
            denominator=total,
            description="referenced_works values that are not arrays.",
            examples=_example_ids(
                records,
                lambda record: record.get("referenced_works") is not None
                and not isinstance(record.get("referenced_works"), list),
            ),
        ),
        QualityCheck(
            name="invalid_cited_by_count",
            category="references",
            severity="error",
            count=sum(
                1
                for record in records
                if not isinstance(record.get("cited_by_count"), int)
                or record.get("cited_by_count") < 0
            ),
            denominator=total,
            description="cited_by_count values that are missing, non-integer, or negative.",
            examples=_example_ids(
                records,
                lambda record: not isinstance(record.get("cited_by_count"), int)
                or record.get("cited_by_count") < 0,
            ),
        ),
        QualityCheck(
            name="empty_referenced_works",
            category="references",
            severity="warn",
            count=sum(1 for record in records if not record.get("referenced_works")),
            denominator=total,
            description="Records with no outgoing references in OpenAlex metadata.",
            examples=_example_ids(records, lambda record: not record.get("referenced_works")),
        ),
        QualityCheck(
            name="duplicate_references_within_paper",
            category="references",
            severity="warn",
            count=sum(
                1
                for record in records
                if isinstance(record.get("referenced_works"), list)
                and len(record["referenced_works"]) != len(set(record["referenced_works"]))
            ),
            denominator=total,
            description="Records with repeated referenced work IDs.",
            examples=_example_ids(
                records,
                lambda record: isinstance(record.get("referenced_works"), list)
                and len(record["referenced_works"]) != len(set(record["referenced_works"])),
            ),
        ),
        QualityCheck(
            name="self_references",
            category="references",
            severity="warn",
            count=sum(
                1
                for record in records
                if isinstance(record.get("referenced_works"), list)
                and record.get("id") in record["referenced_works"]
            ),
            denominator=total,
            description="Records whose referenced_works include their own work ID.",
            examples=_example_ids(
                records,
                lambda record: isinstance(record.get("referenced_works"), list)
                and record.get("id") in record["referenced_works"],
            ),
        ),
        QualityCheck(
            name="missing_doi",
            category="identifiers",
            severity="warn",
            count=sum(1 for record in records if _is_blank(record.get("doi"))),
            denominator=total,
            description="Records without DOI metadata.",
            examples=_example_ids(records, lambda record: _is_blank(record.get("doi"))),
        ),
        QualityCheck(
            name="malformed_doi",
            category="identifiers",
            severity="warn",
            count=sum(
                1
                for record in records
                if not _is_blank(record.get("doi")) and not DOI_RE.match(str(record.get("doi")))
            ),
            denominator=total,
            description="Non-empty DOI values that do not match a basic DOI pattern.",
            examples=_example_ids(
                records,
                lambda record: not _is_blank(record.get("doi"))
                and not DOI_RE.match(str(record.get("doi"))),
            ),
        ),
        QualityCheck(
            name="missing_language",
            category="metadata",
            severity="warn",
            count=sum(1 for record in records if _is_blank(record.get("language"))),
            denominator=total,
            description="Records without detected language metadata.",
            examples=_example_ids(records, lambda record: _is_blank(record.get("language"))),
        ),
        QualityCheck(
            name="malformed_primary_location",
            category="metadata",
            severity="warn",
            count=sum(
                1
                for record in records
                if record.get("primary_location") is not None
                and not isinstance(record.get("primary_location"), dict)
            ),
            denominator=total,
            description="primary_location values that are not objects.",
            examples=_example_ids(
                records,
                lambda record: record.get("primary_location") is not None
                and not isinstance(record.get("primary_location"), dict),
            ),
        ),
        QualityCheck(
            name="malformed_locations",
            category="metadata",
            severity="warn",
            count=sum(
                1
                for record in records
                if record.get("locations") is not None and not isinstance(record.get("locations"), list)
            ),
            denominator=total,
            description="locations values that are not arrays.",
            examples=_example_ids(
                records,
                lambda record: record.get("locations") is not None
                and not isinstance(record.get("locations"), list),
            ),
        ),
        QualityCheck(
            name="missing_primary_source",
            category="metadata",
            severity="warn",
            count=sum(
                1
                for record in records
                if not (
                    isinstance(record.get("primary_location"), dict)
                    and isinstance(record["primary_location"].get("source"), dict)
                    and record["primary_location"]["source"].get("id")
                )
            ),
            denominator=total,
            description="Records without nested primary_location.source.id.",
            examples=_example_ids(
                records,
                lambda record: not (
                    isinstance(record.get("primary_location"), dict)
                    and isinstance(record["primary_location"].get("source"), dict)
                    and record["primary_location"]["source"].get("id")
                ),
            ),
        ),
        QualityCheck(
            name="malformed_open_access",
            category="metadata",
            severity="warn",
            count=sum(
                1
                for record in records
                if record.get("open_access") is not None
                and not isinstance(record.get("open_access"), dict)
            ),
            denominator=total,
            description="open_access values that are not objects.",
            examples=_example_ids(
                records,
                lambda record: record.get("open_access") is not None
                and not isinstance(record.get("open_access"), dict),
            ),
        ),
        QualityCheck(
            name="malformed_concepts",
            category="topics",
            severity="warn",
            count=sum(
                1
                for record in records
                if record.get("concepts") is not None and not isinstance(record.get("concepts"), list)
            ),
            denominator=total,
            description="concepts values that are not arrays.",
            examples=_example_ids(
                records,
                lambda record: record.get("concepts") is not None
                and not isinstance(record.get("concepts"), list),
            ),
        ),
        QualityCheck(
            name="malformed_topics",
            category="topics",
            severity="warn",
            count=sum(
                1
                for record in records
                if record.get("topics") is not None and not isinstance(record.get("topics"), list)
            ),
            denominator=total,
            description="topics values that are not arrays.",
            examples=_example_ids(
                records,
                lambda record: record.get("topics") is not None
                and not isinstance(record.get("topics"), list),
            ),
        ),
    ]

    check_dicts = [check.as_dict() for check in checks]
    status_counts = Counter(check["status"] for check in check_dicts)
    return {
        "record_count": total,
        "observed_fields": observed_fields,
        "expected_fields": expected_fields,
        "field_type_counts": {
            field: _field_type_counts(records, field) for field in observed_fields
        },
        "summary": {
            "total_checks": len(check_dicts),
            "passed_checks": status_counts.get("pass", 0),
            "warning_checks": status_counts.get("warn", 0),
            "error_checks": status_counts.get("error", 0),
            "records_with_any_reference": sum(1 for record in records if record.get("referenced_works")),
            "records_with_any_author": sum(1 for record in records if record.get("authorships")),
        },
        "checks": check_dicts,
    }


def write_quality_report(payload: dict[str, Any], output_path: Path) -> None:
    """Write a human-readable quality report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Data Quality Report",
        "",
        f"Generated from observed raw OpenAlex records on {date.today().isoformat()}.",
        "",
        "No records are removed or transformed by this report.",
        "",
        "## Summary",
        "",
        f"- Records checked: {payload['record_count']}",
        f"- Total checks: {summary['total_checks']}",
        f"- Passed checks: {summary['passed_checks']}",
        f"- Warning checks: {summary['warning_checks']}",
        f"- Error checks: {summary['error_checks']}",
        f"- Records with at least one reference: {summary['records_with_any_reference']}",
        f"- Records with at least one authorship: {summary['records_with_any_author']}",
        "",
        "## Check Results",
        "",
        "| check | category | status | affected | % | description | examples |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]

    for check in payload["checks"]:
        examples = ", ".join(check["examples"]) if check["examples"] else ""
        examples = examples.replace("|", "\\|")
        description = check["description"].replace("|", "\\|")
        lines.append(
            f"| {check['name']} | {check['category']} | {check['status']} | "
            f"{check['count']}/{check['denominator']} | {check['percentage']:.2f} | "
            f"{description} | {examples} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Warnings identify data that the cleaning pipeline must handle explicitly. "
            "Errors indicate fields or structures that would break downstream assumptions if not fixed "
            "or quarantined in later Bronze/Silver/Gold processing.",
            "",
            "Machine-readable results are saved to `reports/results/data_quality_report.json`.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_quality_report(config: dict[str, Any]) -> dict[str, Any]:
    """Load raw records, run quality checks, and write JSON/Markdown outputs."""
    raw_jsonl_path = resolve_project_path(config, config["paths"]["raw_sample_jsonl"])
    json_path = resolve_project_path(config, config["paths"]["data_quality_json"])
    markdown_path = resolve_project_path(config, config["paths"]["data_quality_md"])

    records = load_jsonl(raw_jsonl_path)
    payload = run_quality_checks(records, config["dataset"]["select_fields"])

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_quality_report(payload, markdown_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    payload = generate_quality_report(config)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
