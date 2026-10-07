"""Acquire a deterministic development sample from the OpenAlex Works API."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from scigraph.utils.config import load_config, resolve_project_path

MAX_OPENALEX_SAMPLE_SIZE = 10_000


def _filter_string(filters: dict[str, Any]) -> str:
    filter_parts: list[str] = []
    if filters.get("from_publication_date"):
        filter_parts.append(f"from_publication_date:{filters['from_publication_date']}")
    if filters.get("type"):
        filter_parts.append(f"type:{filters['type']}")
    if filters.get("has_abstract") is not None:
        value = str(bool(filters["has_abstract"])).lower()
        filter_parts.append(f"has_abstract:{value}")
    return ",".join(filter_parts)


def build_openalex_url(
    config: dict[str, Any],
    page: int = 1,
    cursor: str | None = None,
) -> str:
    """Build an OpenAlex Works API URL from config."""
    dataset = config["dataset"]
    sample_size = int(dataset["sample_size"])
    page_size = min(int(dataset.get("api_page_size", sample_size)), sample_size, 200)

    params: dict[str, str | int] = {
        "per-page": page_size,
        "select": ",".join(dataset["select_fields"]),
    }

    if cursor is not None:
        params["cursor"] = cursor
    else:
        params["sample"] = sample_size
        params["seed"] = int(dataset["seed"])
        params["page"] = page

    filters = _filter_string(dataset.get("filters", {}))
    if filters:
        params["filter"] = filters
    if dataset.get("contact_email"):
        params["mailto"] = dataset["contact_email"]

    return f"{dataset['source_url']}?{urlencode(params)}"


def acquire_openalex_sample(config: dict[str, Any]) -> dict[str, Any]:
    """Fetch and save the configured OpenAlex sample as JSONL plus metadata."""
    raw_jsonl_path = resolve_project_path(config, config["paths"]["raw_sample_jsonl"])
    metadata_path = resolve_project_path(config, config["paths"]["raw_metadata_json"])
    raw_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    sample_size = int(config["dataset"]["sample_size"])
    page_size = min(int(config["dataset"].get("api_page_size", sample_size)), sample_size, 200)
    use_cursor_paging = sample_size > MAX_OPENALEX_SAMPLE_SIZE
    acquisition_mode = "cursor" if use_cursor_paging else "sample"
    records_written = 0
    request_urls: list[str] = []
    api_meta: dict[str, Any] = {}
    payload: dict[str, Any] = {}

    page = 1
    cursor: str | None = "*" if use_cursor_paging else None

    with raw_jsonl_path.open("w", encoding="utf-8") as handle:
        while records_written < sample_size:
            request_url = build_openalex_url(config, page=page, cursor=cursor)
            request_urls.append(request_url)
            response = requests.get(request_url, timeout=60)
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                details = response.text[:500]
                raise requests.HTTPError(
                    f"{exc}. OpenAlex response body: {details}", response=response
                ) from exc

            payload = response.json()
            api_meta = payload.get("meta", {})
            page_records = payload.get("results", [])
            if not page_records:
                break

            remaining = sample_size - records_written
            for record in page_records[:remaining]:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
                records_written += 1

            if len(page_records) < page_size:
                break
            if use_cursor_paging:
                next_cursor = api_meta.get("next_cursor")
                if not next_cursor:
                    break
                cursor = str(next_cursor)
            else:
                page += 1

    metadata = {
        "acquisition_mode": acquisition_mode,
        "dataset": config["dataset"]["name"],
        "source_name": config["dataset"]["source_name"],
        "source_url": config["dataset"]["source_url"],
        "documentation_url": config["dataset"]["documentation_url"],
        "license": config["dataset"]["license"],
        "retrieval_datetime_utc": datetime.now(timezone.utc).isoformat(),
        "request_url": request_urls[0] if request_urls else build_openalex_url(config),
        "request_urls": request_urls,
        "configured_sample_size": int(config["dataset"]["sample_size"]),
        "actual_record_count": records_written,
        "seed": int(config["dataset"]["seed"]),
        "filters": config["dataset"].get("filters", {}),
        "raw_sample_jsonl": str(raw_jsonl_path),
        "api_meta": api_meta,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    metadata = acquire_openalex_sample(config)
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
